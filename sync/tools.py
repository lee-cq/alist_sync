# coding: utf8
import logging
import time


def time_2_timestamp(_t: str) -> int:
    """时间戳转换"""
    logging.getLogger('alist.tools').debug('%s input args > _t=%s', __name__, _t)
    if isinstance(_t, str):
        if len(_t) >20:  # 2022-10-24T15:29:14.036070267+08:00
            _t = _t[:19] + 'Z'
        return int(time.mktime(time.strptime(_t, '%Y-%m-%dT%H:%M:%SZ')))
    return int(_t)
