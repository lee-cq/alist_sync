import logging
from pathlib import Path

from sync.operator_json import JsonOperator as Operator
from urllib.parse import urlparse

logger = logging.getLogger('alist.sync.updating_cache')


class UpdatingCache(Operator):
    """"""

    def __init__(self, cache_uri):
        _p = urlparse(cache_uri)
        if _p.scheme.lower() == 'json':
            super().__init__(self.json_op(_p))
        else:
            raise

    @staticmethod
    def json_op(_p):
        """JSON文件位置重写"""
        path = Path(_p.path)
        new_path = 'json://' + path.with_stem(path.stem + '_updating_cache').as_posix()
        logger.info('Rewrite Json File path from <%s> to <%s>', path, new_path, )
        return new_path

    def verify_item_value(self, path, item_value) -> bool:
        """
        :param path:
        :param item_value:
        """
        data = self.search_path(path)
        if isinstance(data, (str, bool)):
            return False
        if isinstance(item_value, int) and isinstance(data, int):
            return False
        return True

    def update_status(self, path, key, value):
        """Update Status key"""
        data = self.search_path(path)
        if not isinstance(data, dict):
            raise TypeError(f'Init Error, {path} should be inited to a dict, rather than type {type(data)}')
        data[key] = value
        if self.is_lock():
            self.unlock()
            self.update_path(path, data)
            self.lock()
        else:
            self.update_path(path, data)
