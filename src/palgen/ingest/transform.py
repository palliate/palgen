def CompressKeys(data, namespace=None, separator='.'):
    if namespace is None:
        namespace = []

    if not isinstance(data, dict):
        return

    if any(not isinstance(v, dict) for v in data.values()):
        yield separator.join(namespace[:-1]), namespace[-1], data
        return

    for key, value in data.items():
        yield from CompressKeys(value, namespace + [key], separator)
