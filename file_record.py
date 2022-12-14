import logging
from pathlib import Path

from back_operator import JsonOperator as Operator
from tools import time_2_timestamp

logger = logging.getLogger('alist.sync.file_record')


class FileRecord(Operator):
    data_model_item = {
        "modified": lambda x: x is None or isinstance(x, int) and x >= 0,
        "size": lambda x: x is None or isinstance(x, int) and x >= 0
    }

    def verify_item_value(self, value: dict) -> bool:
        for key, v in self.data_model_item.items():
            if not v(value[key]):
                logging.getLogger('alist.sync.operator').debug('Error: %s : %s is NOT success ', key, value[key])
                return False
        return True

    def update_path(self, path, item_value: dict):
        if isinstance(item_value['modified'], str):
            item_value['modified'] = time_2_timestamp(item_value['modified'])
        keys = self.data_model_item.keys()
        for _ in list(item_value.keys()):
            if _ not in keys:
                del item_value[_]
        return super().update_path(path, item_value)


if __name__ == '__main__':
    import logging.config, yaml

    logging.config.dictConfig(yaml.safe_load(open('logger_config.yml').read()))
    log = logging.getLogger('alist.sync')
    log.info(f'start file record file. ')
    stat = FileRecord('json:///tmp/tmp.json')  # ('json:///tmp/tmp.json')
    stat.set_item_dirs(['/item'])
    stat.create_path('/item/sub', {'modified': '123', 'size': 222})
    log.info(f'END')
    Path('/tmp/tmp.json').unlink(missing_ok=True)
