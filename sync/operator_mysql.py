#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : operator_mysql.py
@Author     : LeeCQ
@Date-Time  : 2022/11/6 15:52
"""
import logging
import sys
import json
from pathlib import Path
from typing import Iterable

import pymysql

from .operator_base import OperatorBase
from .error import *

__all__ = []

logger = logging.getLogger('alist.sync.operator.mysql')


class MySQLApi:
    """MySQL"""
    logger = logging.getLogger('alist.sync.operator.mysql.api')

    def __init__(self, host, port, user, passwd, db, charset,
                 use_unicode=None, **kwargs):
        super().__init__()
        self.SQL_HOST = host  # 主机
        self.SQL_PORT = port  # 端口
        self.SQL_USER = user  # 用户
        self.SQL_PASSWD = passwd  # 密码
        self.SQL_DB = db  # 数据库
        self.SQL_CHARSET = charset  # 编码
        self.use_unicode = use_unicode
        # 表前缀
        self.TABLE_PREFIX = kwargs.pop('prefix', '')
        self._sql = pymysql.Connect(host=self.SQL_HOST,
                                    port=self.SQL_PORT,
                                    user=self.SQL_USER,
                                    password=self.SQL_PASSWD,  # 可以用 passwd为别名
                                    database=self.SQL_DB,  # 可以用 db    为别名；
                                    charset=self.SQL_CHARSET,
                                    use_unicode=use_unicode,
                                    **kwargs
                                    )
        self.pooled_sql = None

    def set_use_db(self, db_name):
        """设置当前数据库"""
        return self._sql.select_db(db_name)

    def set_charset(self, charset):
        """设置数据库链接字符集"""
        return self._sql.set_charset(charset)

    def set_prefix(self, prefix):
        """设置表前缀"""
        self.TABLE_PREFIX = prefix

    def close(self):
        """关闭数据库连接"""
        self._sql.close()

    def parse_prefix(self, name: str) -> str:
        """返回一个正确的真实的表名称"""
        return name if name.startswith(self.TABLE_PREFIX) else f'{self.TABLE_PREFIX}{name}'

    def get_real_table_name(self, name):
        return self.parse_prefix(name)

    def write_db(self, command, args=None):
        """执行数据库写入操作

        :argument command
        :type args: str, list or tuple
        """
        if self.pooled_sql is not None:
            _sql = self.pooled_sql.connection()
        else:
            _sql = self._sql

        cur = _sql.cursor()  # 使用cursor()方法获取操作游标
        try:
            _c = cur.execute(command, args)
            _sql.commit()  # 提交数据库
            return _c
        except Exception:
            _sql.rollback()
            sys.exc_info()
            raise SqlWriteError(f'操作数据库时出现问题，数据库已回滚至操作前——\n{sys.exc_info()}\n\n{command}')
        finally:
            cur.close()

    # 写入事务
    def write_affair(self, command, args):
        """向数据库写入多行"""
        if self.pooled_sql is not None:
            _sql = self.pooled_sql.connection()
        else:
            _sql = self._sql

        try:
            with _sql.cursor() as cur:  # with 语句自动关闭游标
                _c = cur.executemany(command, args)
                _sql.commit()
            return _c
        except Exception:
            _sql.rollback()
            sys.exc_info()
            raise SqlWriteError("_write_rows() 操作数据库出错，已回滚 \n" + str(sys.exc_info()))

    def read_db(self, command, args=None, result_type=None):
        """执行数据库读取数据， 返回结果

        :param command
        :param args
        :param result_type: 返回的结果集类型{dict, None, tuple, 'SSCursor', 'SSDictCursor'}
        """
        if self.pooled_sql is not None:
            _sql = self.pooled_sql.connection()
        else:
            _sql = self._sql

        ret_ = {dict: pymysql.cursors.DictCursor,
                None: pymysql.cursors.Cursor,
                tuple: pymysql.cursors.Cursor,
                list: pymysql.cursors.Cursor,
                'SSCursor': pymysql.cursors.SSCursor,
                'SSDictCursor': pymysql.cursors.SSDictCursor
                }
        cur = _sql.cursor(ret_[result_type])
        cur.execute(command, args)
        results = cur.fetchall()
        cur.close()
        return results

    # 查表中键的所有信息 - > list
    def _columns(self, table, result_type=None):
        """返回table中列（字段）的所有信息

         +-------+-------+------+------+-----+---------+-------+
         | index |   0   |  1   |   2  |  3  |    4    |   5   |
         +-------+-------+------+------+-----+---------+-------+
         | dict  | Field | Type | Null | Key | Default | Extra |
         +-------+-------+------+------+-----+---------+-------+
        """
        table = self.get_real_table_name(table)
        return self.read_db(f'show columns from `{table}`', result_type=result_type)

    # 查表中的键
    def columns_name(self, table) -> list:
        """返回 table 中的 列名在一个列表中"""
        table = self.get_real_table_name(table)
        return [_c[0].decode() if isinstance(_c[0], bytes) else _c[0] for _c in self._columns(table)]

    # 获取数据库的表名
    def tables_name(self) -> list:
        """由于链接时已经指定数据库，无需再次指定。返回数据库中所有表的名字。"""
        return [_c[0].decode() if isinstance(_c[0], bytes) else _c[0] for _c in self.read_db("show tables")]


class OperatorMySQL(OperatorBase):
    """基于MySQL实现的操作器"""

    def _init(self):
        self.sql = MySQLApi(
            host=self.uri_parse.hostname,
            port=self.uri_parse.port,
            user=self.uri_parse.username,
            passwd=self.uri_parse.password,
            db=self.uri_parse.path,
            charset='utf8'
        )
        self.operator_table = None
        self.create_operator_table()

    def create_operator_table(self):
        """创建操作表"""
        items = ', '.join(f'`{i}` JSON ' for i in self.item_dirs)
        self.sql.write_db(f"CREATE TABLE IF NOT EXISTS `{self.operator_table}` ("
                          f" `sub_path` varchar(256) not null , "
                          f" {items}"
                          f")"
                          )

    def verify_item_value(self, path, item_value) -> bool:
        raise NotImplementedError

    def search_path(self, path):
        """数据类型不定的问题，可能需要额外的操作

        对于 file_record 一定是 dict (json)
        对于 updating_cache 可能是 bool, int, json
        """
        item, sub_path = self.break_path_relative_item_base(path)
        data = self.sql.read_db(f"SELECT {item} FROM {self.operator_table} WHERE `sub_path`='{sub_path}'")[0][0]

        return json.loads(data)['data']

    def search_items_path(self, item_dir) -> Iterable:
        pass

    def all_sub_path(self) -> Iterable:
        for sub in self.sql.read_db(f"SELECT `sub_path` FROM {self.operator_table}"):
            yield sub[0]

    def all_full_path(self, with_value=False) -> Iterable:
        offset = 0
        while True:
            data = self.sql.read_db(f"SELECT * FROM {self.operator_table} LIMIT 20 OFFSET {offset}", result_type=dict)
            if data:
                break
            for sub in data:
                sub_path = sub.pop('sub_path')
                for item, value in sub.items():
                    if with_value:
                        yield Path(item).joinpath(sub_path).as_posix(), value
                    else:
                        yield Path(item).joinpath(sub_path).as_posix()

    def update_path(self, path, item_value):
        pass

    def create_path(self, path, path_value):
        pass

    def delete_path(self, path):
        pass

    def lock(self):
        pass

    def is_lock(self):
        pass

    def unlock(self):
        pass
