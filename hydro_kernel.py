import collections.abc
import sys

# from droplet.client.client import DropletConnection
from ipykernel.ipkernel import IPythonKernel

# import client_utils
# from kernel_functions import run_cell

# DROPLET_EXECUTE_FNAME = 'run_cell'
# HYDRO_ELB_ADDR = 'a5fb01a1c5a5811ea84940e2c3e63f6e-1922551257.us-east-1.elb.amazonaws.com'
# DEVSERVER_IP = '34.239.146.81'


class CachedDict(collections.abc.MutableMapping):
    @property
    def __class__(self):
        return dict
    def __init__(self, dict_to_wrap):
        # dict_to_wrap: the dictionary object to wrap.
        self.dict_to_wrap = dict_to_wrap
        self.dict_cache = dict()

    def __getitem__(self, key, refresh=False):
        print("Getting key ", key)
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
        print("Setting key ", key, " = ", value)
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

    def copy(self):
        return self.dict_to_wrap


class HydroKernel(IPythonKernel):
    # # Kernel info fields
    # implementation = 'IPython on Hydro'
    # implementation_version = '0.1'
    # language_info = {
    #     'name': 'IPython on Hydro',
    #     'version': sys.version.split()[0],
    #     'mimetype': 'text/x-python',
    #     'codemirror_mode': {
    #         'name': 'ipython',
    #         'version': sys.version_info[0]
    #     },
    #     'pygments_lexer': 'ipython3',
    #     'nbconvert_exporter': 'python',
    #     'file_extension': '.py'
    # }

    # banner = "IPython on Hydro"

    def __init__(self, **kwargs):
        kwargs['user_ns'] = CachedDict(dict())
        kwargs['user_ns'] = dict()
        super().__init__(**kwargs)

    # def do_execute(
    #     self,
    #     code, silent,
    #     store_history=True, user_expressions=None, allow_stdin=False,
    # ):
    #     # session_id = 'user_mdemo' # XXX DUMMY SESSION ID for now

    #     out = super().do_execute(code, silent, store_history,
    #                      user_expressions, allow_stdin)
    #     return out

    #     # In this implementation, we bypass the IPython kernel entirely.
    #     # droplet_execute = client_utils.get_or_register_function(
    #     #     DropletConnection(HYDRO_ELB_ADDR, DEVSERVER_IP),
    #     #     run_cell,
    #     #     DROPLET_EXECUTE_FNAME,
    #     # )

    #     # exc_count, outputs = droplet_execute(code, session_id).get()

    #     # for index, (tag, output) in outputs:
    #     #     if tag == 'stdout':
    #     #         sys.stdout.write(output)
    #     #     elif tag == 'stderr':
    #     #         sys.stderr.write(output)
    #     #     else:
    #     #         assert False

    #     reply_content = {}
    #     reply_content[u'status'] = u'ok'
    #     reply_content['execution_count'] = exc_count
    #     reply_content[u'user_expressions'] = {} # XXX unused but also dummy
    #     return reply_content




import sys

if __name__ == '__main__':
    # Remove the CWD from sys.path while we load stuff.
    # This is added back by InteractiveShellApp.init_path()
    if sys.path[0] == '':
        del sys.path[0]

    from ipykernel import kernelapp as app
    app.launch_new_instance(kernel_class=HydroKernel)
