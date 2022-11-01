# coding: utf8
import logging
import time


def time_2_timestamp(_t: str) -> int:
    """时间戳转换"""
    logging.getLogger('alist.tools').debug('%s 输入参数 _t=%s', __name__, _t)
    if isinstance(_t, str):
        return int(time.mktime(time.strptime(_t, '%Y-%m-%dT%H:%M:%SZ')))
    _t: int
    return _t
