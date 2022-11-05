#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : error.py
@Author     : LeeCQ
@Date-Time  : 2022/11/5 22:15
"""


class AlistException(Exception):
    pass


class HTTPRequestException(AlistException):
    pass


class AlistServerException(AlistException):
    pass


class NoAuth(AlistException):
    pass


class BadResponse(AlistException):
    pass


class LoginError(AlistException):
    pass
