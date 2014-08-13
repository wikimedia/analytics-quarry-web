import pymysql
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from models.queryrun import QueryRun
from models.queryresult import QuerySuccessResult, QueryErrorResult, QueryKilledResult
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from connections import Connections
from sqlalchemy.orm import sessionmaker
import time
import yaml
import os


__dir__ = os.path.dirname(__file__)

celery_log = get_task_logger(__name__)

celery = Celery('quarry.web.worker')
celery.conf.update(yaml.load(open(os.path.join(__dir__, "../default_config.yaml"))))
celery.conf.update(yaml.load(open(os.path.join(__dir__, "../config.yaml"))))

conn = session = None


def make_result(cur):
    if cur.description is None:
        return None
    return {
        'headers': [c[0] for c in cur.description],
        'rows': cur.fetchall()
    }


@worker_process_init.connect
def init(sender, signal):
    global conn, session

    conn = Connections(celery.conf)
    celery_log.info("Initialized lazy loaded connections")

    Session = sessionmaker(bind=conn.db_engine)
    session = Session()
    celery_log.info('Initialized query run repository')


@worker_process_shutdown.connect
def shutdown(sender, signal, pid, exitcode):
    global conn
    kill_query.delay(conn.replica.thread_id())
    conn.close_all()
    celery_log.info("Closed all connection")


@celery.task(name='worker.kill_query')
def kill_query(thread_id):
    cur = conn.replica.cursor()
    try:
        cur.execute("KILL QUERY %s", (thread_id, ))
        celery_log.info("Query with thread:%s killed", thread_id)
    except pymysql.InternalError as e:
        if e.args[0] == 1094:  # Error code for 'no such thread'
            celery_log.info("Query with thread:%s died before it could be killed", thread_id)
        else:
            celery_log.exception("Error killing thread:%s", thread_id)
            raise
    finally:
        cur.close()


@celery.task(name='worker.run_query')
def run_query(query_run_id):
    global conn

    cur = False
    start_time = time.clock()
    try:
        celery_log.info("Starting run for qrun:%s", query_run_id)
        qrun = session.query(QueryRun).filter(QueryRun.id == query_run_id).one()
        qrun.status = QueryRun.STATUS_RUNNING
        session.add(qrun)
        session.commit()
        check_result = qrun.rev.is_allowed()
        if check_result is not True:
            celery_log.info("Check result for qrun:%s failed, with message: %s", qrun.id, check_result[0])
            raise pymysql.DatabaseError(0, check_result[1])
        cur = conn.replica.cursor()
        cur.execute(qrun.augmented_sql)
        result = []
        result.append(make_result(cur))
        while cur.nextset():
            result.append(make_result(cur))
        total_time = time.clock() - start_time
        qresult = QuerySuccessResult(qrun, total_time, result, celery.conf.OUTPUT_PATH_TEMPLATE)
        qrun.status = QueryRun.STATUS_COMPLETE
        celery_log.info("Completed run for qrun:%s successfully", qrun.id)
        qresult.output()
        session.add(qrun)
        session.commit()
    except pymysql.DatabaseError as e:
        total_time = time.clock() - start_time
        qresult = QueryErrorResult(qrun, total_time, celery.conf.OUTPUT_PATH_TEMPLATE, e.args[1])
        qrun.status = QueryRun.STATUS_FAILED
        qresult.output()
        session.add(qrun)
        session.commit()
        celery_log.info("Completed run for qrun:%s with failure: %s", qrun.id, e.args[1])
    except SoftTimeLimitExceeded:
        celery_log.info(
            "Time limit exceeded for qrun:%s, thread:%s attempting to kill",
            qrun.id, conn.replica.thread_id()
        )
        total_time = time.clock() - start_time
        kill_query.delay(conn.replica.thread_id())
        qrun.state = QueryRun.STATUS_KILLED
        session.add(qrun)
        session.commit()
        qresult = QueryKilledResult(qrun, total_time, celery.conf.OUTPUT_PATH_TEMPLATE)
        qresult.output()
    finally:
        if cur is not False:
            # It is possible the cursor was never created,
            # so check before we try to close it
            cur.close()
