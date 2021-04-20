import os
import re
import json
from enum import Enum


def _proc_expression(exp):
    if isinstance(exp, list):
        exp = exp[1:] if exp[0] == '' else exp
        return '\n'.join(exp)
    else:
        return exp

class Table_item:

    _format_pat = re.compile(r' Format="(?P<format>\w+)" ')

    class Type(Enum):
        COLUMN = 1
        MEASURE = 2

    def __init__(self, item, item_type):
        self.name = item['name']
        self.type = item_type
        self.dax = _proc_expression(item.get('expression'))
        self.data_type = item.get('dataType')
        annotations = self._proc_annotations(item)
        self.format = annotations.get('Format')
        if self.format is not None:
            self.format = self._format_pat.search(self.format)['format']
        self.source = item.get("sourceColumn")

    def _proc_annotations(self, item):
        annotations = {i['name']: i['value'] for i in item['annotations']}
        return annotations


class Table:

    _source_pat = re.compile(r'\s(?P<schema>\w+)_Schema\{\[Name="(?P<name>\w+)"')

    def __init__(self, path):
        table_json = self._get_table_json(path)
        self.name = table_json['name']
        self.source = self._proc_source(table_json)
        # self.columns
        # self.calc_cols
        # self.measures
        # self.relations

    def _get_table_json(self, path):
        files = [f for f in os.listdir(path) if f[-5:] == '.json']
        if len(files) == 0:
            raise ValueError('Table json not found')
        if len(files) > 1:
            raise ValueError('Ambiguous table json :'+ str(files))
        table_json = os.path.join(path,files[0])
        with open(table_json, 'r') as f:
            return json.load(f)

    def _proc_source(self, table_json):
        source = _proc_expression(table_json['partitions'][0]['source'].get('expression'))
        if source is not None:
            source = self._source_pat.search(source)
        if source is not None:
            return (source['schema'], source['name'])
        else:
            return 'Manual'


