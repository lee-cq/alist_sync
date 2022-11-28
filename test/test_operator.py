#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : test_operator.py
@Author     : LeeCQ
@Date-Time  : 2022/11/28 11:28
"""
import logging.config
import unittest
from pathlib import Path

import yaml

from sync.operator_json import OperatorJson as _OpJson
from sync.operator_mysql import OperatorMySQL as _OpMySQL

TEST_DIR = Path(__file__).absolute().parent

logging.config.dictConfig(yaml.safe_load(TEST_DIR.joinpath('logger.yml').open(encoding='utf8')))


class OperatorJson(_OpJson):

    def verify_item_value(self, path, item_value) -> bool:
        return True


class OperatorMySQL(_OpMySQL):

    def verify_item_value(self, path, item_value) -> bool:
        return True


class TestOperator(unittest.TestCase):
    """操作器测试"""

    @classmethod
    def setUpClass(cls) -> None:
        operators = [
            OperatorJson(cache_uri=f'json://{TEST_DIR.joinpath("tmp/test_operator.json").as_posix()}'),
            OperatorMySQL(cache_uri=f'mysql://test:test123456@localhost:3306/alist_sync?table=alist_sync_unittest'),
        ]

        [op.set_item_dirs('/test_1') for op in operators]
        [op.set_item_dirs('/test_2') for op in operators]

        cls.operators = operators

    def sub_test(self, func, *args, msg='', **kwargs):
        """插入测试"""
        for op in self.operators:
            with self.subTest(operator=type(op), msg=msg):
                func(*args, **kwargs)

    def test_(self):
        pass
