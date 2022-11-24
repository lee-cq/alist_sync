import abc
import logging
import urllib.parse
from pathlib import Path
from typing import List, Iterable

logger = logging.getLogger('alist.sync.operator')


class OperatorBase(metaclass=abc.ABCMeta):

    def __init__(self, cache_uri):
        self.cache_uri = cache_uri
        self.uri_parse = urllib.parse.urlparse(cache_uri)
        self._item_dirs = set()
        self.name = type(self).__name__
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
        logger.info('%s set items dir success, %s', self.name, self._item_dirs)

    def break_path_relative_item_base(self, path):
        """从Alist总是得到完整的绝对路径，我们需要将Path 分解为 sub_path & item_path"""
        path = Path(path)
        for item_dir in self.item_dirs:
            if path.is_relative_to(item_dir):
                if path.relative_to(item_dir).as_posix():
                    raise ValueError(f'sub_path 必须是一个有效的字符串.')
                return str(item_dir), path.relative_to(item_dir).as_posix()
        raise ValueError(f'Path 应该相对与一个 item_dirs {self.item_dirs}')

    @abc.abstractmethod
    def search_path(self, path) -> dict:
        """查询一个路径"""

    def select_path(self, path):
        return self.search_path(path)

    @abc.abstractmethod
    def search_items_path(self, item_dir) -> Iterable:
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def all_sub_path(self) -> Iterable:
        """返回全部的sub_path"""

    @abc.abstractmethod
    def all_full_path(self, with_value=False) -> Iterable:
        """返回全路径"""

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

    @abc.abstractmethod
    def lock(self):
        """锁定"""

    @abc.abstractmethod
    def is_lock(self):
        """"""

    @abc.abstractmethod
    def unlock(self):
        """"""
