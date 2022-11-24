#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : operator_json.py
@Author     : LeeCQ
@Date-Time  : 2022/11/5 21:28
"""
import abc
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


class JsonOperator(OperatorBase, abc.ABC):
    """"""

    def _init(self):
        self.data = dict()

        self.path = Path(self.uri_parse.path)
        if self.path.exists():
            logger.info('%s > 从文件 %s 加载JSON对象', self.name, self.path)
            self.data = loads(self.path.read_text(encoding='utf8') or '{}')

        self._thread()
        atexit.register(self.dumps_data)
        logger.debug('Json Operation Init Success . ')

    def __del__(self):
        self.dumps_data()
        logger.debug('%s is EOL.', self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close = True
        self.__del__()

    def __enter__(self):
        return self

    def _thread(self):

        def dump_in_thread():
            logger.info(f'{self.name} sub_thread is running .')
            hash_data = hash(str(self.data))
            while True:
                time.sleep(5)
                if hash_data != hash(str(self.data)):
                    self.dumps_data()
                    hash_data = hash(str(self.data))

        threading.Thread(target=dump_in_thread, name=f'{self.name}_dump_data', daemon=True).start()
        logger.info(f"{self.name}'s sub thread is started, main thead will go on.")

    def dumps_data(self):
        lens = self.path.write_text(dumps(self.data, ensure_ascii=False), encoding='utf8')
        logger.info('Save to %s, size %d', str(self.path), lens)

    def search_items_path(self, item_dir) -> Iterable:
        """"""
        for it in self.data[item_dir]:
            yield it

    def all_sub_path(self) -> Iterable:
        """返回全部的sub_path"""
        return {x for i in self.item_dirs for x in self.search_items_path(i)}

    def all_full_path(self, with_value=False) -> Iterable:
        for item in self.item_dirs:
            for sub, value in self.data.get(item, dict()).items():
                if with_value:
                    yield Path(item).joinpath(sub).as_posix(), value
                else:
                    yield Path(item).joinpath(sub).as_posix()

    def search_path(self, path, default=None):
        try:
            _item, _sub_path = self.break_path_relative_item_base(path)
            return self.data.get(_item, dict()).get(_sub_path, default)
        except ValueError:
            return self.data.get(path, default)

    def update_path(self, path, item_value):
        if self.is_lock():
            raise BlockingIOError
        item_dir, sub_path = self.break_path_relative_item_base(path)
        if self.verify_item_value(path, item_value):
            if self.data.get(item_dir) is None:
                self.data[item_dir] = dict()
            self.data[item_dir][sub_path] = item_value
            logger.info('update data[%s][%s] = %s', item_dir, sub_path, item_value)
        else:
            raise ValueError(f'item_value is Error, {self.name}: {path} -> {item_value}')

    def create_path(self, path, item_value):
        return self.update_path(path, item_value)

    def delete_path(self, path):
        if self.is_lock():
            raise BlockingIOError
        try:
            item_dir, sub_path = self.break_path_relative_item_base(path)
            del self.data[item_dir][sub_path]
        except ValueError:
            del self.data[path]
        except KeyError:
            logger.debug('%s do not exists.', path)

    def lock(self):
        self.data['lock'] = True
        logger.debug('%s is Locked. ', self.name)

    def is_lock(self):
        return self.data.get('lock', False)

    def unlock(self):
        try:
            del self.data['lock']
        except KeyError:
            pass
        finally:
            logger.info('%s is unlocked.', self.name)
