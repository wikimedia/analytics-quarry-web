import codecs as _codecs

_codecs.register_error("strict", _codecs.lookup_error("surrogateescape"))
