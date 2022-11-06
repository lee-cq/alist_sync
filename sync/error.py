#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : error.py
@Author     : LeeCQ
@Date-Time  : 2022/11/6 11:21
"""


class AlistSyncException(Exception):
    """"""


class SyncException(AlistSyncException):
    """"""


class OperatorError(AlistSyncException):
    """"""


class NotParseSuccessError(SyncException, ValueError):
    """Not Parse Success for UpdatingCache"""


class SqlWriteError(OperatorError):
    """"""
