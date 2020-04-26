
import time
import sys
import zmq

import cloudpickle as pickle


from ipykernel.ipkernel import IPythonKernel


# The five Jupyter sockets:
#   - Shell: input for code and magic
#   - IOPub: output
#   - Control: input for shutdown/restart/debug
#   - stdin: input for raw_input()
#   - Heartbeat: input for heartbeat
# and all messages are like
# {
#     'header' : {
#         'msg_id' : str, # typically UUID, must be unique per message
#         'session' : str, # typically UUID, should be unique per session
#         'username' : str,
#         'date': str, # ISO 8601 timestamp for when the message is created
#         'msg_type' : str, # e.g. 'execute_request'
#         'version' : '5.0', # the message protocol version
#     },

#     'content' : dict,
#         # message_type dependent.

#     'parent_header' : dict,
#         # copy of the header of the message that “caused” the current message.

#     'msg_id' : str,
#     'msg_type' : str,
#         # The msg's unique identifier and type are always stored in the header,
#         # but the Python implementation also copies them to the top level.

#     'metadata' : dict, # not often used
#     'buffers': list, # not often used
# }

# A Kernel that forwards requests to a serverless backend.
class ServerlessKernelClient(IPythonKernel):
    implementation = 'Serverless Kernel'
    implementation_version = '0.1'
    language_info = {
        'name': 'python',
        'version': sys.version.split()[0],
        'mimetype': 'text/x-python',
        'codemirror_mode': {
            'name': 'ipython',
            'version': sys.version_info[0]
        },
        'pygments_lexer': 'ipython3',
        'nbconvert_exporter': 'python',
        'file_extension': '.py'
    }

    @property
    def banner(self):
        return self.shell.banner + "\nServerless edition, by UC Berkeley RISELab, 2020"

    IOPUB_SOCK_BIND = "tcp://*:5555"
    IOPUB_SOCK_CONNECT = "tcp://localhost:5555"

    def do_execute(self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
    ):



        # Create sockets for iopub forwarding.
        # TODO: shell and control too.
        context = zmq.Context()
        iopub_receiver_socket = context.socket(zmq.DEALER)
        iopub_receiver_socket.bind(self.IOPUB_SOCK_BIND)

        # Run the serverless run_cell function.
        # XXX testing version
        import proxying_client
        # res = proxying_client.execute({'iopub': self.IOPUB_SOCK_CONNECT}, code)
        import base64
        import subprocess
        nargs = [{'iopub': self.IOPUB_SOCK_CONNECT}, code]
        nargs = pickle.dumps(nargs)
        nargs = base64.b64encode(nargs)
        res = subprocess.run(['./proxying_client.py', nargs], stdout=subprocess.PIPE)
        res = res.stdout
        res = base64.b64decode(res)
        res = pickle.loads(res)

        # Get iopub results. Process and forward.
        done = False

        # contents = {'execution_count': 10,
        #             'data': {'text/plain': repr('hello')},
        #             'metadata': {}}
        # self.session.send(self.iopub_socket, 'execute_result', contents,
        #                   parent={}, ident=b'execute_result')
        while not done:
            try:
                msg = iopub_receiver_socket.recv(flags=zmq.NOBLOCK)
                msg = pickle.loads(msg)
                msg_type = msg['header']['msg_type']
                if msg_type == 'status':
                    status = msg["content"]["execution_state"]
                    if status == 'idle':
                        done = True
                # print(repr(msg))
                # print(repr(msg['header']['msg_type']))
                # print(repr(bytes(msg['msg_type'], encoding='utf-8')))
                self.session.send(
                    self.iopub_socket,
                    msg['header']['msg_type'],
                    content=msg['content'],
                    ident=bytes(msg['msg_type'], encoding='utf-8'),
                    # header=msg['header'],
                    # parent=msg['parent_header'],
                )

            except zmq.ZMQError as e:
                time.sleep(0.05)

        # Get the serverless run_cell results.
        # XXX noop, we have it already

        return res['content']

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=ServerlessKernelClient)
