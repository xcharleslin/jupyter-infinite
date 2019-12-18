#!/usr/bin/env python3.6

import sys

from droplet.client.client import DropletConnection
from ipykernel.ipkernel import IPythonKernel

import client_utils
from kernel_functions import run_cell

DROPLET_EXECUTE_FNAME = 'run_cell0'
HYDRO_ELB_ADDR = 'ae69a62461c4911ea937a0eba282ec08-1435775530.us-east-1.elb.amazonaws.com'
DEVSERVER_IP = '34.239.146.81'

class HydroKernel(IPythonKernel):
    # Kernel info fields
    implementation = 'IPython on Hydro'
    implementation_version = '0.1'
    language_info = {
        'name': 'IPython on Hydro',
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

    banner = "IPython on Hydro"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_id = 'user0' # XXX DUMMY SESSION ID for now
        self.droplet_client = DropletConnection(
            HYDRO_ELB_ADDR, DEVSERVER_IP)
        self.droplet_execute = client_utils.get_or_register_function(
            self.droplet_client, run_cell, DROPLET_EXECUTE_FNAME)

    def do_execute(
        self,
        code, silent,
        store_history=True, user_expressions=None, allow_stdin=False,
    ):
        # In this implementation, we bypass the IPython kernel entirely.
        exc_count, outputs = self.droplet_execute(code, self.session_id).get()

        for index, (tag, output) in outputs:
            if tag == 'stdout':
                sys.stdout.write(output)
            elif tag == 'stderr':
                sys.stderr.write(output)
            else:
                assert False

        reply_content = {}
        reply_content[u'status'] = u'ok'
        reply_content['execution_count'] = exc_count
        reply_content[u'user_expressions'] = {} # XXX unused but also dummy
        return reply_content



if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=HydroKernel)
