#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : operator_json.py
@Author     : LeeCQ
@Date-Time  : 2022/11/5 21:28
"""
import atexit
import logging
import time
import threading
from pathlib import Path
from typing import Iterable
from json import loads, dumps

from .operator_base import OperatorBase

__all__ = ['JsonOperator']

logger = logging.getLogger('alist.sync.operator.json')


class JsonOperator(OperatorBase):
    """"""

    def _init(self):
        self.data = dict()

        self.path = Path(self.uri_parse.path)
        if self.path.exists():
            logger.info('%s > 从文件 %s 加载JSON对象', type(self).__name__, self.path)
            self.data = loads(self.path.read_text(encoding='utf8') or '{}')

        self._thread()
        atexit.register(self.dumps_data)
        logger.debug('Json Operation Init Success . ')

    def __del__(self):
        self.dumps_data()
        logger.debug('%s is EOL.', type(self).__name__)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close = True
        self.__del__()

    def __enter__(self):
        return self

    def _thread(self):
        self_name = type(self).__name__

        def dump_in_thread():
            logger.info(f'{self_name} sub_thread is running .')
            hash_data = hash(str(self.data))
            while True:
                time.sleep(5)
                if hash_data != hash(str(self.data)):
                    self.dumps_data()
                    hash_data = hash(str(self.data))

            # logger.info(f'{self_name} dump thread break. ')

        threading.Thread(target=dump_in_thread, name=f'{self_name}_dump_data', daemon=True).start()
        logger.info(f"{self_name}'s sub thread is started, main thead will go on.")

    def dumps_data(self):
        lens = self.path.write_text(dumps(self.data, ensure_ascii=False), encoding='utf8')
        logger.info('Save to %s, size %d', str(self.path), lens)

    def search_items(self, item_dir) -> Iterable:
        """"""
        for it in self.data[item_dir]:
            yield it

    def all_sub_path(self) -> Iterable:
        """返回全部的sub_path"""
        return {x for i in self.item_dirs for x in self.search_items(i)}

    def all_full_path(self) -> Iterable:
        for item in self.item_dirs:
            for sub in self.data.get(item, dict()).keys():
                yield Path(item).joinpath(sub).as_posix()

    def verify_item_value(self, path, item_value) -> bool:
        raise NotImplementedError()

    def search_path(self, path, default=None):
        try:
            _item, _sub_path = self.verify_path_relative_item_base(path)
            return self.data.get(_item, dict()).get(_sub_path, default)
        except ValueError:
            return self.data.get(path, default)

    def select_path(self, path):
        return self.search_path(path)

    def update_path(self, path, item_value):
        if self.is_lock():
            raise BlockingIOError
        item_dir, sub_path = self.verify_path_relative_item_base(path)
        if self.verify_item_value(path, item_value):
            if self.data.get(item_dir) is None:
                self.data[item_dir] = dict()
            self.data[item_dir][sub_path] = item_value
            logger.info('update data[%s][%s] = %s', item_dir, sub_path, item_value)
        else:
            raise ValueError(f'item_value 验证失败, {type(self).__name__} -> {item_value}')

    def create_path(self, path, item_value):
        if self.is_lock():
            raise BlockingIOError
        return self.update_path(path, item_value)

    def delete_path(self, path):
        if self.is_lock():
            raise BlockingIOError
        try:
            item_dir, sub_path = self.verify_path_relative_item_base(path)
            del self.data[item_dir][sub_path]
        except ValueError:
            del self.data[path]
        except KeyError:
            logger.debug('%s do not exists.', path)

    def lock(self):
        self.data['lock'] = True

    def is_lock(self):
        return self.data.get('lock', False)

    def unlock(self):
        try:
            del self.data['lock']
        except KeyError:
            pass
