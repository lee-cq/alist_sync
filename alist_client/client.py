#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : client.py
@Author     : LeeCQ
@Date-Time  : 2022/11/5 22:19
"""

import http.client
import logging
import urllib.parse
from json import dumps, loads
from pathlib import Path
from urllib.request import urlopen, Request

from .error import *

logger = logging.getLogger('alist.client')


class AlistApi:
    login = '/auth/login'
    me = '/me'

    fs_list = '/fs/list'
    fs_get = '/fs/get'
    fs_dirs = '/fs/dirs'
    fs_create_file = '/fs/put'
    fs_mkdir = '/fs/mkdir'
    fs_rename = '/fs/rename'
    fs_move = '/fs/move'
    fs_copy = '/fs/copy'
    fs_remove = '/fs/remove'
    fs_form = '/fs/form'
    fs_link = '/fs/link'
    fs_add_aria2 = '/fs/add_aria2'


class _Client:
    """Alist 请求客户端"""

    def __init__(self, base_url: str, ):

        self.base_url = base_url[:-1] if base_url.endswith('/') else base_url

        self.headers = dict()
        self._init()

        self.me_info = dict()

    def _init(self):
        self.headers['User-Agent'] = 'AlistClient/Python 0.1'
        self.headers['Content-Type'] = 'application/json;charset=UTF-8'

    def urlopen(self, method, uri, json=None, headers=None, data=None):
        if data is not None and json is not None:
            raise ValueError('json 和 data 不能同时提供')
        if not isinstance(data, (str, bytes, bytearray, type(None))):
            raise ValueError('data 必须是 str, bytes, bytearray')

        url = self.url_json(uri)
        headers = headers if headers else dict()
        [headers.update({k: v}) for k, v in self.headers.items() if k not in headers]
        data = data.encode() if isinstance(data, str) else data

        request = Request(method=method, url=url, headers=headers, data=data or dumps(json).encode())
        logger.debug('REQUEST: %s %s --> header=%s  data=%s', method, url, headers, json)
        resp = urlopen(request)
        return self.verify_response(resp)

    def url_json(self, api):
        api = api if api.startswith('/') else api + '/'
        return self.base_url + api

    def set_token(self, token):
        self.headers.update(Authorization=token)

    @staticmethod
    def verify_response(resp: http.client.HTTPResponse) -> dict:
        """验证响应信息"""
        resp_data = resp.read().decode()
        logger.debug('RESPONSE: %s --> [%d] %s', resp.geturl(), resp.getcode(), resp_data)
        resp_json = loads(resp_data)
        if resp.getcode() == 200 and resp_json['code'] == 200:
            return resp_json['data']
        elif resp.getcode() == 403 or resp_json['code'] == 403:
            raise NoAuth(f'{resp_json["code"]}: {resp_json["message"]}')
        elif resp.getcode() // 100 == 5 or resp_json['code'] // 100 == 5:
            raise AlistServerException(f'{resp_json["code"]}: {resp_json["message"]}')
        else:
            raise HTTPRequestException(f'{resp_json["code"]}: {resp_json["message"]}')

    def me(self) -> dict:
        """检查权限"""
        me_info = self.urlopen(method='GET', uri=AlistApi.me) or dict()
        self.me_info.update(me_info)
        return me_info

    def login(self, user, passwd, opt=''):
        """登陆"""

        data = {
            "username": user,
            "password": passwd,
            "otp_code": opt
        }
        data = self.urlopen(method='POST', uri=AlistApi.login, json=data)
        if data:
            self.set_token(data['token'])
            if self.me().get('username') == user:
                logger.info('%s 登陆成功。', user)
            else:
                logger.error('%s 登陆失败 ... ', user)
                raise LoginError('%s 登陆失败 ... ', user)
        else:
            raise


class _ClientFs(_Client):

    def fs_list(self, path, page=0, per_page=10, refresh_token=False):
        """列出指定位置的全部内容"""
        data = {
            "path": path,
            "page": page,
            "per_page": per_page,
            "refresh": refresh_token
        }
        return self.urlopen('POST', AlistApi.fs_list, json=data)

    def fs_list_iter(self, path, refresh_token=False):
        """返回生成器"""
        page = 0
        while True:
            res_data = self.fs_list(path, page=page, per_page=20, refresh_token=refresh_token)
            if not res_data.get('content'):
                break
            for i in res_data.get('content'):
                yield i
            page += 1

    def fs_get(self, path):
        """获取文件或目录的详细信息"""
        data = {
            "path": path,
        }
        return self.urlopen('POST', AlistApi.fs_get, json=data)

    def fs_other(self):
        """"""
        raise NotImplementedError()

    def fs_dir(self, path, force_root=False):
        """列出指定位置中的目录"""
        data = {
            "path": path,
            "force_root": force_root
        }
        return self.urlopen('POST', AlistApi.fs_dirs, json=data)

    def fs_create_file(self, path, data):
        """创建文件"""
        path = urllib.parse.quote_plus(path)
        return self.urlopen('PUT', AlistApi.fs_create_file, headers={'file-path': path}, data=data) is None

    def fs_mkdir(self, path, exist_ok=True, parents=True):
        """创建目录"""
        Path().mkdir()
        data = {
            'path': path
        }
        return self.urlopen('POST', AlistApi.fs_mkdir, json=data) is None

    def fs_rename(self, path, new_name):
        """重命名文件或目录"""
        data = {
            "path": path,
            "name": new_name
        }
        return self.urlopen('POST', AlistApi.fs_rename, json=data)

    def fs_move(self, src_dir, dst_dir, *names):
        """移动文件或目录"""
        data = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": names
        }
        return self.urlopen('POST', AlistApi.fs_move, json=data)

    def fs_copy(self, src_dir, dst_dir, *names):
        """移动文件或目录"""
        data = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": names
        }
        return self.urlopen('POST', AlistApi.fs_copy, json=data)

    def fs_remove(self, _dir, *names):
        """移除文件或目录"""
        data = {"dir": _dir, "names": names}
        return self.urlopen('POST', AlistApi.fs_remove, json=data)

    def fs_from(self):
        """"""
        raise NotImplementedError

    def fs_link(self):
        """"""
        raise NotImplementedError

    def fs_add_aria2(self):
        """"""
        raise NotImplementedError


class ClientAdmin(_Client):
    pass


class Client(_ClientFs):
    """客户端集成"""
    pass
