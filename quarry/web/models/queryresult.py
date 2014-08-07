import json
import os
import datetime
import decimal


class MoreAcceptingJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return super(MoreAcceptingJSONEncoder, self).default(obj)


class QueryResult(object):
    def __init__(self, query_run, path_template, total_time):
        self.query_run = query_run
        self.path_template = path_template
        self.total_time = total_time

    def output(self):
        path = self.path_template % (self.query_run.rev.query.user_id, self.query_run.id)
        self.output_data['query_run'] = {
            'id': self.query_run.id,
            'user': self.query_run.rev.query.user_id
        }
        self.output_data['time'] = self.total_time
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'w') as f:
            json.dump(self.output_data, f, cls=MoreAcceptingJSONEncoder)


class QuerySuccessResult(QueryResult):
    def __init__(self, query_run, total_time, result, path_template):
        super(QuerySuccessResult, self).__init__(query_run, path_template, total_time)
        self.result = result

    def output(self):
        self.output_data = {
            'result': 'ok',
            'data': self.result
        }
        super(QuerySuccessResult, self).output()


class QueryErrorResult(QueryResult):
    def __init__(self, query_run, total_time, path_template, error):
        super(QueryErrorResult, self).__init__(query_run, path_template, total_time)
        self.error = error

    def output(self):
        self.output_data = {
            'result': 'error',
            'error': self.error
        }
        super(QueryErrorResult, self).output()


class QueryKilledResult(QueryResult):
    def __init__(self, query_run, total_time, path_template):
        super(QueryKilledResult, self).__init__(query_run, path_template, total_time)

    def output(self):
        self.output_data = {
            'result': 'killed'
        }
        super(QueryKilledResult, self).output()
