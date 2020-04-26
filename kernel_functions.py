

def run_cell(droplet_client, code_str, namespace):
    import ast
    import sys
    import time
    import cloudpickle as cp
    import collections.abc
        # https://docs.python.org/3/library/collections.abc.html

    import anna.lattices


    """
    CachedDict provides a caching wrapper around any object
    that exposes a dict interface.

    Does not ensure freshness of get().
    """
    class CachedDict(collections.abc.MutableMapping):
        def __init__(self, dict_to_wrap):
            # dict_to_wrap: the dictionary object to wrap.
            self.dict_to_wrap = dict_to_wrap
            self.dict_cache = dict()

        def __getitem__(self, key, refresh=False):
            # If we are asking for a refresh,
            # or item is not cached, fetch it.
            # Then, serves the item from cache.
            # Note: This does not deal with staleness.
            if refresh or (key not in self.dict_cache):
                self.dict_cache[key] = self.dict_to_wrap[key]
                # If this causes a KeyError from dict_to_wrap,
                # we want it to propagate upwards, so we leave it uncaught.
            return self.dict_cache[key]

        def __setitem__(self, key, value):
            # Write through to backing dict.
            self.dict_to_wrap[key] = value
            # Write to cache too.
            self.dict_cache[key] = value

        def __delitem__(self, key):
            del self.dict_to_wrap[key]
            del self.dict_cache[key]

        def __iter__(self):
            # Currently: just bypass the cache entirely.
            return self.dict_to_wrap.__iter__()

        def __len__(self):
            # Currently: just bypass the cache entirely.
            return self.dict_to_wrap.__len__()

    """
    HydroBackedDict is a dict whose contents are backed by
    the Hydro KVS instead of residing in process memory.
    """
    class HydroBackedDict(collections.abc.MutableMapping):
        # namespace is the permanent global namespace
        # that will be used to store this dict in Hydro.
        def __init__(self, droplet_client, namespace):
            self.droplet_client = droplet_client
            self.namespace = namespace

        def __getitem__(self, key):
            # Convert the key into a global key.
            global_key = self._get_global_key(key)
            # Use this key to get the raw bytes from the KVS.
            value_bytes = self.droplet_client.get(global_key)
            if value_bytes is None: raise KeyError(key)
            # Deserialize the value.
            return cp.loads(value_bytes)

        # key: str
        # value: any Python value
        def __setitem__(self, key, value):
            # Convert the key to a global key.
            key = self._get_global_key(key)
            # Serialize the value.
            value = cp.dumps(value)
            # Store it into the kvs.
            self.droplet_client.put(key, value)

        def __delitem__(self, key):
            raise NotImplementedError
        def __iter__(self):
            raise NotImplementedError
        def __len__(self):
            raise NotImplementedError

        # Helper that converts a key for this dict
        # to a global key "<namespace>:key:<key>".
        def _get_global_key(self, key):
            return "{}:key:{}".format(self.namespace, key)

    # Capture stdout and stderr.
    output = []
    class logger:
        def __init__(self, tag):
            self.tag = tag
        def write(self, data):
            output.append((self.tag, data))
    sys.stdout = logger('stdout')
    sys.stderr = logger('stderr')

    # Initialize the program state dictionary.
    hydro_user_ns = HydroBackedDict(droplet_client, namespace)
    # user_ns = CachedDict(hydro_user_ns)
    user_ns = hydro_user_ns  # Disable app-level caching for now.

    # Parse the code to execute.
    nodelist = ast.parse(code_str).body

    # The semantics of cell execution are that we run all statements,
    # but only return the result of the last one.
    nodes_exec = nodelist[:-1]
    nodes_interactive = nodelist[-1:]
    bytecodes = []
    for node in nodes_exec:
        node = ast.Module([node])
        bytecode = compile(node, '<string>', 'exec')
        bytecodes.append(bytecode)

    for node in nodes_interactive:
        node = ast.Interactive([node])
        bytecode = compile(node, '<string>', 'single')
        bytecodes.append(bytecode)

    try:
        for bytecode in bytecodes:
            exec(bytecode, globals(), user_ns)
    except:
        sys.stderr.write(str(sys.exc_info()[1]))

    # XXX DROPLET HACK
    # Droplet can't handle empty lists, so we append None.
    # output.append(None)
    # XXX DROPLET HACK
    # Droplet sorts lists, so we number the list.
    output = list(enumerate(output))

    # Also, get the execution count.
    exc_count = droplet_client.get(
        '{}:exc_count'.format(namespace))
    if exc_count is None: exc_count = 0
    exc_count += 1
    droplet_client.put(
        '{}:exc_count'.format(namespace), exc_count)

    return (exc_count, output)
