import re


VALID_DB_NAMES = re.compile(
    r"^(?:(?:(?:centralauth|meta|[0-9a-z_]*wik[a-z]+)(?:_p)?)|quarry)$"
)


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


def valid_dbname(dbname):
    """Test a dbname string to see if it looks valid."""
    try:
        if VALID_DB_NAMES.match(dbname) is not None:
            return True
    except TypeError:
        pass
    return False
