#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : t_sync.py
@Author     : LeeCQ
@Date-Time  : 2022/11/5 22:45
"""
import threading
import logging.config

import yaml

from sync.sync import Sync

logging.config.dictConfig(yaml.safe_load(open('logger_config.yml').read()))
logger = logging.getLogger('alist.test.sync')



def sync_():
    conf = yaml.safe_load(open('config.yml').read())
    with Sync(conf['sync_group'][0]) as s:
        s.scan_update_file()
    print('off')
    for t in threading.enumerate():
        print(t.name, t.is_alive(), t.isDaemon())


if __name__ == '__main__':
    sync_()
