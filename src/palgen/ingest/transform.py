#pylint: disable=invalid-name

def CompressKeys(data, namespace=None, separator='.'):
    # TODO this is remaining from the old TOML ingest - update, document and test this
    if namespace is None:
        namespace = []

    if not isinstance(data, dict):
        return

    if any(not isinstance(v, dict) for v in data.values()):
        yield separator.join(namespace[:-1]), namespace[-1], data
        return

    for key, value in data.items():
        yield from CompressKeys(value, namespace + [key], separator)
