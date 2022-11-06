#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : alist_sync.py
@Author     : LeeCQ
@Date-Time  : 2022/10/29 17:23
"""
import json
import logging
import time
from pathlib import PurePosixPath as Path

from alist_client import Client as AlistClient

from .file_record import FileRecord
from .tools import time_2_timestamp
from .updating_cache import UpdatingCache


class Sync:
    """同步主要逻辑

    config: {
      "name": "t1",
      "alist_prefix": "https://localhost/api",
      "alist_username": "test",
      "alist_password": "test",
      "alist_token": "",
      "item": [
        "/onedrive/tmp/",
        "/local/tmp/"
      ],
      "cache_uri": "json:///tmp/alist_sync_t1.json"
    }

    """
    logger = logging.getLogger('alist.sync.sync')

    def __init__(self, config: dict):

        self.items = config.get('items')

        self.files_record = FileRecord(config['cache_path'])
        self.update_cache = UpdatingCache(config['cache_path'])

        self.update_cache.set_item_dirs(self.items)
        self.files_record.set_item_dirs(self.items)

        self.alist_client = AlistClient(config['alist_prefix'])

        if config.get('alist_token'):
            self.alist_client.set_token(config.get('alist_token'))
        elif config.get('alist_username'):
            self.logger.info('login user<%s> to %s', config['alist_username'], config['alist_prefix'])
            self.alist_client.login(config['alist_username'], config['alist_password'])
        else:
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('%s will exiting', type(self).__name__)
        self.__del__()

    def __del__(self):
        self.logger.debug('%s will deleting', type(self).__name__)

    # Init
    # ============================
    # Scan update file

    def scan_update_file(self):
        """扫描更新的文件"""
        if self.update_cache.is_lock():
            self.logger.warning('UpdatingCache is locked, skip scan update files. ')
            return

        self.logger.info('Begin Scan Sync dirs, %s', self.items)
        for item in self.items:
            self.scan_file_in_item(item)

        self.logger.info('Begin parse what file need Update.')
        for sub_path in self.update_cache.all_sub_path():
            if sub_path == '.':
                continue

            self.scan_file_parse(sub_path)

        if any(not isinstance(self.update_cache.select_path(i), int) for i in self.update_cache.all_full_path()):
            self.update_cache.lock()
        else:
            self.update_cache.unlock()
            raise NotParseSuccessError()

    def scan_file_parse(self, sub_path):
        paths = {Path(i).joinpath(sub_path).as_posix() for i in self.items}
        source_path = self.get_dict_max_key({k: self.update_cache.search_path(k, 0) for k in paths})
        if not source_path:
            self.logger.info('%s < not changed, do not need sync ...', sub_path)
            [self.update_cache.delete_path(p) for p in paths]
            return

        self.update_cache.delete_path(source_path)
        [self.update_cache.update_path(p,
                                       {'source': source_path,
                                        'status': UpdateStat.init,
                                        'time': time.time()
                                        })
         for p in paths if p != source_path
         ]

    def scan_file_in_item(self, in_dir):
        """扫描更新文件"""
        self.logger.info('Scan Dir %s', in_dir)
        if self.update_cache.search_path(in_dir):  # 已经缓存的跳过
            self.logger.info('The dir %s has cached, skip ... ', in_dir)
            return

        for file_dic in self.alist_client.fs_list_iter(in_dir):
            path = Path(in_dir).joinpath(file_dic.get('name')).as_posix()
            if self.update_cache.search_path(path) is not None:
                self.logger.debug('%s not None, skip .', path)
                continue
            self.logger.debug('%s is dir -- %s', path, file_dic.get('is_dir'))
            if file_dic.get('is_dir'):
                self.scan_file_in_item(path)
            else:
                old_p = self.files_record.select_path(path)
                op_time = old_p.get('update_time', 0) if old_p else 0
                if op_time == 0:
                    self.files_record.update_path(path, file_dic)
                self.update_cache.update_path(path, time_2_timestamp(file_dic.get('modified')) - op_time)
        self.update_cache.update_path(in_dir, True)

    def get_dict_max_key(self, dic: dict):
        """Get Key from a dict"""
        self.logger.debug('Get max value %s', dic)
        if not all(type(i) == int for i in dic.values()):
            return None
        max_val = max(dic.values())
        if max_val == 0:
            return None
        return list(dic.keys())[list(dic.values()).index(max_val)]

    # Scan File
    # ==============================
    # Move Old File To Backup Dir

    def verify_copying(self, path):
        """验证正在进行copy

        :return Noting, Doing, Down
        """

    def copy_file(self, sor, target):
        """拷贝文件

        1. 验证目标文件是否存在  是 -> 2,   否 -> 3
        2. 移动目标到 /@alist_sync_older_file
                     产生2个文件： 1. 源文件(name_id)  2. name_id.json
             2.1 复制文件到 /@alist_sync_old_file/
             2.2 生成源文件信息 到 /@alist_sync_old_file/.json
             2.3 验证上述文件存在   -->  删除源文件
        3. 开始 fs_copy()   -- fs_copy 实际是在alist 上生成一个task, 进行异步的复制
        4. 调用 task/copy/undone 接口，检查是否已经添加 task
        5. 将 目标path update_time  设置为 upping
        """

    def sync_files(self):
        """update"""


def test_copy():
    """"""
    pass
