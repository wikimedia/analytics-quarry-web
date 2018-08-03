import re
import codecs

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


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


def slugify(text, delim='-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = codecs.encode(word, 'translit/long')
        if word:
            result.append(word)
    return str(delim.join(result))
