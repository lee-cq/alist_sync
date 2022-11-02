import abc
import atexit
import logging
import time
import urllib.parse
from pathlib import Path
from typing import List, Iterable

logger = logging.getLogger('alist.sync.operator')


class _OperatorBase(metaclass=abc.ABCMeta):

    def __init__(self, cache_uri):
        self.uri_parse = urllib.parse.urlparse(cache_uri)
        self._item_dirs = set()
        self._init()

    @abc.abstractmethod
    def _init(self):
        """"""
        raise NotImplementedError()

    @abc.abstractmethod
    def verify_item_value(self, path, item_value) -> bool:
        """验证值是否正确
        :param path:
        :param item_value
        """
        raise NotImplementedError()

    @property
    def item_dirs(self):
        if self._item_dirs:
            return self._item_dirs
        raise ValueError('在调用之前，必须set_item_dir')

    def add_item_dir(self, item_dir):
        self._item_dirs.add(item_dir)

    def set_item_dirs(self, *item_dirs):
        x = []
        for i in item_dirs:
            if isinstance(i, (list, tuple, set, List)):
                x.extend(i)
            else:
                x.append(i)

        self._item_dirs = set(x)
        logger.info('set items dir success, %s', self._item_dirs)

    def verify_path_relative_item_base(self, path):
        """从Alist总是得到完整的绝对路径，我们需要将Path 分解为 sub_path & item_path"""
        path = Path(path)
        for item_dir in self.item_dirs:
            if path.is_relative_to(item_dir):
                return str(item_dir), path.relative_to(item_dir).as_posix()
        raise ValueError(f'Path 应该相对与一个 item_dirs {self.item_dirs}')

    @abc.abstractmethod
    def search_path(self, path) -> dict:
        """查询一个路径"""

    @abc.abstractmethod
    def search_items(self, item_dir) -> Iterable:
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def all_sub_path(self) -> Iterable:
        """返回全部的sub_path"""

    @abc.abstractmethod
    def update_path(self, path, item_value):
        """更新一个路径,
        path 是一个绝对路径, 且必须相对于一个item_dir
        """

    @abc.abstractmethod
    def create_path(self, path, path_value):
        """创建一个新的"""

    @abc.abstractmethod
    def delete_path(self, path):
        pass


class JsonOperator(_OperatorBase, ):
    """"""

    def _init(self):
        self.data = dict()
        self._close = False

        self.path = Path(self.uri_parse.path)
        if self.path.exists():
            from json import loads
            self.data = loads(self.path.read_text(encoding='utf8'))
        atexit.register(self.dumps_data)
        self._thread()
        logger.debug('Json Operation Init Success . ')

    def __del__(self):
        self.dumps_data()
        self._close = True
        logger.debug('%s is EOL.', type(self).__name__)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __enter__(self):
        return self

    def _thread(self):

        def dump_in_thread():
            logger.info('sub_thread is running .')
            hash_data = hash(str(self.data))
            while not self._close:
                time.sleep(5)
                if hash_data != hash(str(self.data)):
                    self.dumps_data()
                    hash_data = hash(str(self.data))

            logger.info(f'dump thread break. ')

        from threading import Thread

        Thread(target=dump_in_thread, name='dump_data').start()
        logger.info('定时Save 线程已开启.')

    def dumps_data(self):
        from json import dumps
        lens = self.path.write_text(dumps(self.data, ensure_ascii=False), encoding='utf8')
        logger.info('Save to %s, size %d', str(self.path), lens)

    def search_items(self, item_dir) -> Iterable:
        """"""
        for it in self.data[item_dir]:
            yield it

    def all_sub_path(self) -> Iterable:
        """返回全部的sub_path"""
        return {x for i in self.item_dirs for x in self.search_items(i)}

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
        item_dir, sub_path = self.verify_path_relative_item_base(path)
        if self.verify_item_value(path, item_value):
            if self.data.get(item_dir) is None:
                self.data[item_dir] = dict()
            self.data[item_dir][sub_path] = item_value
            logger.info('update data[%s][%s] = %s', item_dir, sub_path, item_value)
        else:
            raise ValueError(f'item_value 验证失败。')

    def create_path(self, path, item_value):
        return self.update_path(path, item_value)

    def delete_path(self, path):
        try:
            item_dir, sub_path = self.verify_path_relative_item_base(path)
            del self.data[item_dir][sub_path]
        except ValueError:
            del self.data[path]


class MysqlOperator:
    def __init__(self):
        pass


class RedisOperator:
    def __init__(self, ):
        # import redis
        pass


class SqliteOperator:
    def __init__(self):
        pass

# class MongoOperator(_OperatorBase):
#     """"""

# class Operator:
#     """缓存对象，处理多驱动的标准接口。
#
#     数据结构: [{name: , base_path1: , base_path2: }, {} ... ]
#     """
#
#     def __new__(cls, cache_uri, *args, **kwargs):
#         urlparse = urllib.parse.urlparse(cache_uri)
#         logger = logging.getLogger('operator')
#         logger.debug(f'{urlparse.scheme = } ')
#         if urlparse.scheme == 'json':
#             logger.debug(type(cls.__dict__))
#             # cls.__dict__.setdefault(JsonOperator.__dict__)
#             cls.set_attr(JsonOperator)
#             return JsonOperator(urlparse.path)
#         elif urlparse.scheme == 'redis':
#             pass
#         else:
#             raise
#
#     @classmethod
#     def set_attr(cls, c):
#         """"""
#         for name, func in c.__dict__.items():
#             if name not in cls.__dict__.keys():
#                 cls.__setattr__(cls, name, func)
