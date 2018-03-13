import contextlib
import json
import os
import signal
import yaml

import pymysql

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from celery.utils.log import get_task_logger

from connections import Connections
from models.queryrun import QueryRun
from results import SQLiteResultWriter


__dir__ = os.path.dirname(__file__)

celery_log = get_task_logger(__name__)

celery = Celery('quarry.web.worker')
celery.conf.update(yaml.load(open(os.path.join(__dir__, "../default_config.yaml"))))
try:
    celery.conf.update(yaml.load(open(os.path.join(__dir__, "../config.yaml"))))
except IOError:
    # Is ok if we can not load config.yaml
    pass

conn = None


# TODO: use python stopit after Halfak teaches me how to package properly
@contextlib.contextmanager
def raise_after(seconds, exc_gen):
    def handler(*args, **kwargs):
        raise exc_gen()

    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, handler)
    old_time = signal.alarm(seconds)

    try:
        yield
    finally:
        assert signal.getsignal(signal.SIGALRM) == handler
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(old_time)


class CustomQueryError(Exception):
    pass


@worker_process_init.connect
def init(*args, **kwargs):
    global conn

    conn = Connections(celery.conf)
    celery_log.info("Initialized lazy loaded connections")


@worker_process_shutdown.connect
def shutdown(*args, **kwargs):
    global conn
    conn.close_all()
    celery_log.info("Closed all connection")


@celery.task(name='worker.run_query')
def run_query(query_run_id):
    global conn

    cur = None
    try:
        celery_log.info("Starting run for qrun:%s", query_run_id)
        qrun = conn.session.query(QueryRun).filter(QueryRun.id == query_run_id).one()
        qrun.status = QueryRun.STATUS_RUNNING
        conn.session.add(qrun)
        conn.session.commit()
        check_result = qrun.rev.is_allowed()
        if check_result is not True:
            celery_log.info("Check result for qrun:%s failed, with message: %s", qrun.id, check_result[0])
            raise pymysql.DatabaseError(0, check_result[1])
        cur = conn.replica.cursor()
        cur.execute('SELECT CONNECTION_ID();')
        qrun.extra_info = json.dumps({'connection_id': cur.fetchall()[0][0]})
        conn.session.add(qrun)
        conn.session.commit()
        cur.execute(qrun.augmented_sql)
        output = SQLiteResultWriter(qrun, celery.conf.OUTPUT_PATH_TEMPLATE)
        try:
            with raise_after(60, lambda: CustomQueryError(
                'Too many results! Did you add some conditions or a limit to '
                'the number of results? If you want tens of thousands or more '
                'results, such as the titles of all articles, Wikimedia Dumps '
                'at dumps.wikimedia.org will be a better option.')
            ):  # T188564
                while True:
                    if cur.description:
                        output.start_resultset([c[0] for c in cur.description], cur.rowcount)
                        rows = cur.fetchmany(10)
                        while rows:
                            output.add_rows(rows)
                            rows = cur.fetchmany(10)
                        output.end_resultset()
                    if not cur.nextset():
                        break
                output.close()
        except Exception:
            # Destroy the file, we won't need it.
            output.destroy()
            raise
        qrun.status = QueryRun.STATUS_COMPLETE
        qrun.extra_info = json.dumps({'resultsets': output.get_resultsets()})
        output = None
        celery_log.info("Completed run for qrun:%s successfully", qrun.id)
        conn.session.add(qrun)
        conn.session.commit()
    except pymysql.InternalError as e:
        if e[0] == 1317:  # Query interrupted
            celery_log.info(
                "Time limit exceeded for qrun:%s, thread:%s attempting to kill",
                qrun.id, conn.replica.thread_id()
            )
            qrun.status = QueryRun.STATUS_KILLED
            conn.session.add(qrun)
            conn.session.commit()
        else:  # Surfacing it to the user is always better than just silently failing
            write_error(qrun, e[1])
    except pymysql.DatabaseError as e:
        write_error(qrun, e[1])
    except pymysql.OperationalError as e:
        write_error(qrun, e[1])
    except CustomQueryError as e:
        write_error(qrun, e[0])
    finally:
        conn.close_session()

        if cur is not None:
            # It is possible the cursor was never created,
            # so check before we try to close it
            try:
                cur.close()
            except pymysql.OperationalError as e:
                if e[0] == 2013:
                    # Lost connection to MySQL server during query
                    pass
                else:
                    raise


def write_error(qrun, error):
    qrun.status = QueryRun.STATUS_FAILED
    qrun.extra_info = json.dumps({'error': error})
    conn.session.add(qrun)
    conn.session.commit()
    celery_log.info("Completed run for qrun:%s with failure: %s", qrun.id, error)
