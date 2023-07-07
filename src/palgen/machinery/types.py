def normalize_type(type_: type):
    return getattr(type_, '__origin__', type_)


def issubtype(type_: type, bases: type | tuple[type, ...]):
    return issubclass(normalize_type(type_), bases)
