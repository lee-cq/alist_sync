import logging
from pathlib import Path

from back_operator import JsonOperator as Operator
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

    def json_op(self, _p):
        path = Path(_p.path)
        new_path = 'json://' + path.with_stem(path.stem + '_updating_cache').as_posix()
        logger.info('Rewrite Json File path from <%s> to <%s>', path, new_path, )
        return new_path

    def verify_item_value(self, item_value) -> bool:
        """验证的"""
        # TODO 验证器
        return True
