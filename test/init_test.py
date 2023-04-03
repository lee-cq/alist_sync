#!/bin/env python3
import os
from pathlib import Path
from subprocess import run as exec_run

base_path = Path(__file__).parent.absolute()

alist_server_path = base_path.joinpath('alist_server')
alist_server_path.mkdir(exist_ok=True)

alist_data_path = alist_server_path.joinpath('data')
alist_data_path.mkdir(exist_ok=True)


def windows_install():
    """Windows"""
    if not alist_server_path.joinpath('alist.exe').exists():
        a= os.popen(f'cd {alist_server_path};'
                 f'curl -O https://github.com/alist-org/alist/releases/download/v3.3.0/alist-windows-4.0-amd64.zip;'
                 f'powershell -c " Expand-Archive alist-windows-4.0-amd64.zip ."').read()
        print(a)



def linux_amd64_install():
    """Linux"""
    if not alist_server_path.joinpath('alist').exists():
        exec_run(['/bin/bash', '-c',
                  f'cd {alist_server_path}'
                  'wget https://github.com/alist-org/alist/releases/download/v3.3.0/alist-linux-musl-amd64.tar.gz &&'
                  'tar -xzvf alist-linux-musl-amd64.tar.gz'
                  ])


def install_alist():
    """Install"""


if __name__ == '__main__':
    windows_install()