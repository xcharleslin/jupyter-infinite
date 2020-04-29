

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
