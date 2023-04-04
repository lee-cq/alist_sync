# 导入:
import os

import dotenv
from sqlalchemy import Table, Column, String, Enum, Integer, DATETIME, JSON, MetaData
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session, mapped_column

__all__ = ["metadata_obj", "BACKUP_STATUS", "FILE_STATUS", "TASK_STATUS",
           "table_files", "table_backups", "table_tasks",
           "File", "Backup", "Task"
           ]

metadata_obj = MetaData()

BACKUP_STATUS = Enum('init', 'scan')
FILE_STATUS = Enum('init')
TASK_STATUS = Enum('init')

table_files = Table(
    "files",
    metadata_obj,
    Column("file_id", String(64), primary_key=True, doc='文件的ID'),
    Column("path", String(256), doc='文件的路径'),
    Column("backup_id", String(64), doc='备份ID'),
    Column("task_id", String(64), doc='任务ID'),
    Column("status", FILE_STATUS, doc='文件状态'),
    Column("data", JSON(), doc='文件属性'),
    Column("operation_time", DATETIME(), doc='操作时间')
)

table_backups = Table(
    'backup',
    metadata_obj,

    Column("_id", Integer(), primary_key=True, autoincrement=True, doc='自增主键'),
    Column("backup_id", String(64), unique=True, doc='备份ID'),
    Column("backup_status", BACKUP_STATUS, doc='备份任务的状态'),
    Column("start_time", DATETIME(), doc='开始时间'),
    Column("update_time", DATETIME(), doc='最近更新时间'),

)

table_tasks = Table(
    'tasks',
    metadata_obj,
    Column("_id", Integer(), primary_key=True, autoincrement=True, doc='自增主键'),
    Column("task_id", String(129), unique=True, doc='backup_id.file_id 组合'),
    Column("source_drive", String(256), doc='源驱动器'),
    Column("target_drive", String(256), doc='目标驱动器'),
    Column("status", TASK_STATUS, doc='任务状态'),
    Column("create_time", DATETIME(), doc='创建时间'),
    Column("update_time", DATETIME(), doc='跟新时间'),
    Column("data", JSON(), default='{}', doc='任务的JSON数据'),
)


class ORMBase(DeclarativeBase):
    __abstract__ = True
    metadata = metadata_obj

    @classmethod
    def __table_cls__(cls, name, metadata_obj, *arg, **kw):
        return Table(f"my_{name}", metadata_obj, *arg, **kw)

    def add(self, session: Session):
        """"""
        with session:
            session.add(self)
            session.commit()


class File(ORMBase):
    __tablename__ = 'file'

    file_id: str = mapped_column(String(64), primary_key=True, doc='文件的ID')

    path = mapped_column(String(256), doc='文件的路径')
    backup_id = mapped_column(String(64), doc='备份ID')
    task_id = mapped_column(String(64), doc='任务ID')
    status = mapped_column(FILE_STATUS, doc='文件状态')
    data = mapped_column(JSON(), doc='文件属性')
    operation_time = mapped_column(DATETIME(), doc='操作时间')


class Backup(ORMBase):
    __tablename__ = 'backup'

    _id = mapped_column(Integer(), primary_key=True, autoincrement=True, doc='自增主键')
    backup_id = mapped_column(String(64), unique=True, doc='备份ID')
    backup_status = mapped_column(BACKUP_STATUS, doc='备份任务的状态')
    start_time = mapped_column(DATETIME(), doc='开始时间')
    update_time = mapped_column(DATETIME(), doc='最近更新时间')


class Task(ORMBase):
    __tablename__ = 'task'

    _id = mapped_column(Integer(), primary_key=True, autoincrement=True, doc='自增主键'),
    task_id = mapped_column(String(129), unique=True, doc='backup_id.file_id 组合'),
    source_drive = mapped_column(String(256), doc='源驱动器'),
    target_drive = mapped_column(String(256), doc='目标驱动器'),
    status = mapped_column(TASK_STATUS, doc='任务状态'),
    create_time = mapped_column(DATETIME(), doc='创建时间'),
    update_time = mapped_column(DATETIME(), doc='跟新时间'),
    data = mapped_column(JSON(), default='{}', doc='任务的JSON数据'),


if __name__ == '__main__':
    from sqlalchemy import create_engine

    dotenv.load_dotenv(r'C:\code\alist_copy\.env')

    url = os.getenv('SQLALCHEMY_URL')

    eng = create_engine(url)
    db_session = sessionmaker(bind=eng)

    session = db_session()
    session.get(table_files, )
    metadata_obj.create_all(bind=eng, )

