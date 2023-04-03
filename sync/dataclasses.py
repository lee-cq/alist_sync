# 导入:
from sqlalchemy import Column, String, Enum, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TableFilesBase(Base):
    __table__ = 'files'

    path = Column(String(256), unique=True, doc='文件的路径')
    operator_id = Column(String(64), default=None, doc='操作ID')
    operator_status = Column(Enum(), default='', doc='操作状态')
    operator_time = Column(Integer(), default='', doc='操作时间')
