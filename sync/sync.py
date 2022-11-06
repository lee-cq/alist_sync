#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : alist_sync.py
@Author     : LeeCQ
@Date-Time  : 2022/10/29 17:23
"""
import hashlib
import logging
import threading
import time
from json import dumps
from pathlib import PurePosixPath as Path
from queue import Queue

import alist_client.error
from alist_client import Client as AlistClient

from .file_record import FileRecord
from .tools import time_2_timestamp
from .updating_cache import UpdatingCache
from .error import *


class UpdateStat:
    """"""
    init = 'Init'
    moving_old = 'MovingOld'
    create_old_info = 'CreateOldInfo'
    moved_old = 'MovedOld'
    copying_new = 'CopyingNew'
    copied_new = 'CopiedNew'
    end = 'END'


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
      "backup_dir_name": "@alist_sync_backup"
    }

    """
    logger = logging.getLogger('alist.sync.sync')

    def __init__(self, config: dict):

        self.items = config.get('items')
        self.alist_sync_backup_dir = '.alist_sync_backup'

        self.files_record = FileRecord(config['cache_path'])
        self.update_cache = UpdatingCache(config['cache_path'])

        self.queue_copy_new = Queue(maxsize=10)
        self.queue_copy_verify = Queue(maxsize=10)

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

        self.mkdir_items_backup_dir()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('%s will exiting', type(self).__name__)
        self.__del__()

    def __del__(self):
        self.logger.debug('%s will deleting', type(self).__name__)

    def mkdir_items_backup_dir(self):
        for i in self.items:
            path = Path(i).joinpath(self.alist_sync_backup_dir).as_posix()
            self.alist_client.fs_mkdir(path)

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
            if file_dic.get('name') == self.alist_sync_backup_dir:
                self.logger.debug('skip %s', self.alist_sync_backup_dir)
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

    def sync(self):
        """同步 Main"""
        self.scan_update_file()
        if not self.update_cache.is_lock():
            raise NotParseSuccessError()

        threading.Thread(target=self.move_old_file, name='move_old_file').start()
        threading.Thread(target=self.verify_moving_file, name='verify_move').start()
        # threading.Thread(target=self.sync_new_file, name='sync_new_file').start()
        # threading.Thread(target=self.verify_copying, name='verify_copying').start()

    def move_old_file(self):
        """"""
        for target_path, data in self.update_cache.all_full_path(with_value=True):
            if not isinstance(data, dict):
                self.logger.info('%s\' data is not a dict, skip. (%s)', target_path, type(data))
                continue

            if data['status'] != UpdateStat.init:
                self.logger.info('%s\' status not init, skip. (%s)', target_path, data['status'])
                continue

            self.move_a_old_file(target_path)

    @staticmethod
    def del_old_file_info_item(old_fs_info: dict) -> dict:
        save_keys = ["name", "size", "modified", "sign", "type", "provider"]
        for k in old_fs_info.copy().keys():
            if k in save_keys:
                del old_fs_info[k]
        return old_fs_info

    def move_a_old_file(self, target_path):
        try:
            old_fs_info = self.alist_client.fs_get(target_path)
        except alist_client.error.AlistServerException as _e:
            self.update_cache.update_status(target_path, 'status', UpdateStat.moved_old)
            return

        try:
            item_dir, sub_path = self.update_cache.break_path_relative_item_base(target_path)
            path_hash = hashlib.md5(target_path.encode()).hexdigest()

            old_fs_info = self.del_old_file_info_item(old_fs_info)
            old_fs_info['path'] = target_path
            old_fs_info['hash'] = path_hash
            self.update_cache.update_status(target_path, 'target_old_info', old_fs_info)

            self.alist_client.fs_move(
                src_dir=Path(target_path).parent.as_posix(),
                dst_dir=Path(item_dir).joinpath(self.alist_sync_backup_dir).as_posix(),
                name=Path(target_path).name
            )
            self.alist_client.fs_rename(
                Path(item_dir).joinpath(self.alist_sync_backup_dir).joinpath(Path(target_path).name).as_posix(),
                path_hash + Path(target_path).suffix
            )
            self.update_cache.update_status(target_path, 'status', UpdateStat.moving_old)
            self.logger.info('moving file [%s -> %s]', target_path,
                             Path(item_dir).joinpath(self.alist_sync_backup_dir).joinpath(path_hash).as_posix()
                             )
        except KeyError:
            raise

    def verify_moving_file(self):
        while True:
            all_for = []
            for target_path, data in self.update_cache.all_full_path(with_value=True):
                item_dir, sub_path = self.update_cache.break_path_relative_item_base(target_path)
                path_hash = hashlib.md5(target_path.encode()).hexdigest()
                backup_path = Path(item_dir).joinpath(f'{self.alist_sync_backup_dir}/{path_hash}').with_suffix(
                    Path(target_path).suffix).as_posix()

                all_for.append(data.get('status') != UpdateStat.moving_old)
                if data.get('status') != UpdateStat.moving_old:
                    continue

                try:
                    self.alist_client.fs_get(backup_path)
                    self.alist_client.fs_create_file(Path(backup_path).with_suffix('.json'), dumps(data.get('target_old_info')))
                    self.update_cache.update_status(target_path, 'status', UpdateStat.moved_old)
                    self.logger.info('moved file [ %s -> %s , INFO_FILE: %s]', target_path, backup_path,
                                     Path(backup_path).with_suffix('.json'))
                except alist_client.error.AlistServerException:
                    pass

            time.sleep(5)

            if all(all_for):
                self.logger.info('No have Moving Status\'s Task, %s has stopped.', __name__)
                break

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
