# coding: utf8
import datetime
import logging
import time

logger = logging.getLogger('alist.tools')


def time_2_timestamp(_t: str) -> int:
    """时间戳转换"""
    logger.debug('%s input args > _t=%s', __name__, _t)
    if isinstance(_t, str):
        if len(_t) > 20:  # 2022-10-24T15:29:14.036070267+08:00
            _t = _t[:19] + 'Z'
        return int(time.mktime(time.strptime(_t, '%Y-%m-%dT%H:%M:%SZ')))
    return int(_t)


def timestamp_2_time(_t: int = None) -> str:
    """时间戳转时间字符串"""
    logger.debug('%s input args > _t=%s', __name__, _t)

    if _t is None:
        _t = time.time()
    return datetime.datetime.fromtimestamp(_t).strftime('%Y-%m-%dT%H:%M:%SZ')
