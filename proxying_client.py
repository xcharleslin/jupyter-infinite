#!/usr/bin/python3



# TODO: this needs to launch kernels using custom dicts.

# client_sockets: {
#   'iopub': <str>
# }
def initialize(client_sockets):

    import cloudpickle as pickle
    import time

    import zmq

    from jupyter_core.application import JupyterApp
    from jupyter_client.consoleapp import JupyterConsoleApp

    class ProxyingClient(JupyterApp, JupyterConsoleApp):
        def initialize(self, argv=None):
            self.kernel_name = 'cool-python'
            super(ProxyingClient, self).initialize(argv)
            JupyterConsoleApp.initialize(self)

        def prepare_client_sockets(self, client_sockets):
            context = zmq.Context()
            self.client_iopub_socket = context.socket(zmq.DEALER)
            self.client_iopub_socket.connect(client_sockets['iopub'])


        # ... -> shell message: dict
        # Executes code, taking the same input as jupyter_client.KernelClient,
        # but directly returns the execute_reply shell message.
        def execute(
            self,
            code,
            silent=False,
            store_history=True,
            user_expressions=None,
            allow_stdin=None,
            stop_on_error=True,
        ):
            def _execute():
                # Most of the logic here was reverse engineered
                # from jupyter_console/ptshell.py

                _wait_for_kernel_start()

                msg_id = self.kernel_client.execute(
                    code, silent, store_history, user_expressions,
                    allow_stdin, stop_on_error,
                )

                _handle_messages()

                # Handle execute reply.
                if not self.kernel_client.shell_channel.msg_ready():
                    raise
                msg = self.kernel_client.shell_channel.get_msg()
                # raise Exception(repr(msg))
                return msg

            def _wait_for_kernel_start():
                # Wait for an idle status on the iopub channel.
                ready = False
                while not ready:
                    iopub_msg = self.kernel_client.iopub_channel.get_msg()
                    if _is_idle_message(iopub_msg):
                        ready = True

                # Flush the shell channel.
                while self.kernel_client.shell_channel.msg_ready():
                    self.kernel_client.shell_channel.get_msg()

            def _handle_messages():
                done = False

                # TODO: handle input request messages.

                # Handle iopub messages.
                while not done:
                    # Sleep for a bit so we aren't busy waiting.
                    time.sleep(0.05)

                    if not self.kernel_client.is_alive():
                        # TODO handle
                        raise

                    # Process and forward iopub messages.
                    while self.kernel_client.iopub_channel.msg_ready():
                        iopub_msg = self.kernel_client.iopub_channel.get_msg()
                        if _is_idle_message(iopub_msg):
                            done = True
                        self.client_iopub_socket.send(pickle.dumps(iopub_msg))



            def _is_idle_message(iopub_msg):
                msg_type = iopub_msg['header']['msg_type']
                if msg_type == 'status':
                    status = iopub_msg["content"]["execution_state"]
                    if status == 'idle':
                        return True
                return False

            return _execute()



    app = ProxyingClient.instance()
    app.initialize()
    app.start()
    app.prepare_client_sockets(client_sockets)
    return app


def execute(client_sockets, code):
    app = initialize(client_sockets)
    execute_reply = app.execute(code)
    app.kernel_client.shutdown()
    return execute_reply





def main():
    import base64
    import sys
    import cloudpickle as pickle
    nargs = sys.argv[1]
    nargs = base64.b64decode(nargs)
    nargs = pickle.loads(nargs)
    res = execute(*nargs)
    res = pickle.dumps(res)
    res = base64.b64encode(res)
    res = str(res,encoding='utf-8')
    sys.stdout.write(res)


if __name__ == '__main__':
    main()
