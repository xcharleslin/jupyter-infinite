

class ExecutionPlatform:
    def remote_execute(self):
        raise NotImplementedError

    IOPUB_SOCK_BIND = None
    IOPUB_SOCK_CONNECT = None


# A local-process-based execution platform for testing.
class LocalPlatform(ExecutionPlatform):
    IOPUB_SOCK_BIND = "tcp://*:5555"
    IOPUB_SOCK_CONNECT = "tcp://localhost:5555"

    class FakeFuture:
        def __init__(self, x):
            self.x = x
        def get(self):
            return self.x

    def remote_execute(self, code):
        import base64
        import subprocess
        import cloudpickle as pickle
        import proxying_client
        nargs = [{'iopub': self.IOPUB_SOCK_CONNECT}, code]
        nargs = pickle.dumps(nargs)
        nargs = base64.b64encode(nargs)
        res = subprocess.run(['./proxying_client.py', nargs], stdout=subprocess.PIPE)
        res = res.stdout
        res = base64.b64decode(res)
        res = pickle.loads(res)
        return self.FakeFuture(res)


from cloudburst.client.client import CloudburstConnection
from proxying_client import execute
class CloudburstPlatform(ExecutionPlatform):
    IOPUB_SOCK_BIND = "tcp://*:5555"
    IOPUB_SOCK_CONNECT = "tcp://{}:5555"

    # The Cloudburst function name for remote_execute.
    CLOUDBURST_FNAME_EXECUTE = 'run_cell'

    def __init__(self, caller_ip, cloudburst_addr):
        self.caller_ip = caller_ip
        self.cloudburst_addr = cloudburst_addr

    # Helper to get-or-register functions with Cloudburst.
    def _get_or_register_function(self, func_name, func):
        cloudburst_client = CloudburstConnection(self.cloudburst_addr, self.caller_ip)
        cloud_func = cloudburst_client.get_function(func_name)

        if cloud_func is None:
            # print("Function '{}' not found in Hydro. Registering..."
            #     .format(func_name))
            # Hack to get cloudpickle to serialize the whole function.
            func.__module__ = '__main__'
            cloud_func = cloudburst_client.register(func, func_name)
            if not cloud_func:
                raise Exception("Function registration failed.")

        return cloud_func

    def remote_execute(self, code):
        def execute_cloudburst(cloudburst, client_sockets, code):
            return execute(client_sockets, code)
        cloudburst_execute = self._get_or_register_function(
            self.CLOUDBURST_FNAME_EXECUTE, execute_cloudburst)

        client_sockets = {'iopub': self.IOPUB_SOCK_CONNECT.format(self.caller_ip)}
        future = cloudburst_execute(client_sockets, code)
        return future
