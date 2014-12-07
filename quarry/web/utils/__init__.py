def datetime_json_formatter(dt):
    try:
        return dt.isoformat()
    except AttributeError:
        raise TypeError


def to_json_formatter(dt):
    try:
        return dt.to_json()
    except AttributeError:
        raise TypeError


def json_formatter(dt):
    for formatter in [datetime_json_formatter, to_json_formatter]:
        try:
            return formatter(dt)
        except TypeError:
            pass
    raise TypeError(dt)
