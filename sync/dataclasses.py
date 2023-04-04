# 导入:
from sqlalchemy import Column, String, Enum, Integer, DATETIME, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

BACKUP_STATUS = Enum()
FILE_STATUS = Enum()
TASK_STATUS = Enum()


class TableFilesBase(Base):
    """文件表"""
    __table__ = 'files'

    file_id = Column(String(64), primary_key=True, doc='文件的ID')
    path = Column(String(256), unique=True, doc='文件的路径')
    backup_id = Column(String(64), default=None, doc='操作ID')
    backup_status = Column(Enum(), default='', doc='操作状态')
    backup_time = Column(Integer(), default='', doc='操作时间')


class TableBackup(Base):
    """备份表"""
    __table__ = 'backup'

    _id = Column(Integer(), primary_key=True, autoincrement=True, doc='自增主键')
    backup_id = Column(String(64), unique=True, doc='备份ID')
    status = Column(Enum(), doc='备份任务的状态')
    start_time = Column(DATETIME(), doc='开始时间')
    update_time = Column(DATETIME(), doc='最近更新时间')


class TableTasks(Base):
    """任务表"""
    __table__ = 'tasks'

    _id = Column(Integer(), primary_key=True, autoincrement=True, doc='自增主键')
    task_id = Column(String(129), unique=True, doc='backup_id.file_id 组合')
    source_drive = Column(String(256), doc='源驱动器')
    target_drive = Column(String(256), doc='目标驱动器')
    status = Column(Enum(), doc='任务状态')
    create_time = Column(DATETIME(), doc='创建时间')
    update_time = Column(DATETIME(), doc='跟新时间')
    data = Column(JSON(), doc='任务的JSON数据')


if __name__ == '__main__':
    pass
