import os
import re
import json
import logging
from enum import Enum

from code.view import Tb_name


def _proc_expression(exp):
    if isinstance(exp, list):
        exp = exp[1:] if exp[0] == '' else exp
        return '\n'.join(exp)
    else:
        return exp

def _proc_annotations(item):
    annotations = {i['name']: i.get('value') for i in item['annotations']}
    return annotations

class Folder:
    def __init__(self, name, level=0):
        self.level = level
        self.name = name
        self.folders = {}
        self.measures = []


    def add(self, measure, path):
        if path:
            if path[0] not in self.folders:
                self.folders[path[0]] = Folder(path[0], self.level+1)
            self.folders[path[0]].add(measure, path[1:])
        else:
            self.measures.append(measure)


class Table_item:

    _format_pat = re.compile(r'\sFormat="(?P<format>\w+)"')

    class Type(Enum):
        COLUMN = 1
        MEASURE = 2

    def __init__(self, item, item_type, table):
        self.table = table
        self.name = item['name']
        self.type = item_type
        self.dax = _proc_expression(item.get('expression'))
        self.data_type = item.get('dataType')
        annotations = _proc_annotations(item)
        self.format = annotations.get('Format')
        if self.format is not None:
            try:
                self.format = self._format_pat.search(self.format)['format']
            except TypeError:
                logging.warning(f'Could not extract format for {self.table} - {self.name}')
                self.format = ''
        self.source = item.get("sourceColumn")


class Table:

    _source_pat = re.compile(r'\s(?P<schema>\w+)_Schema\{\[Name="(?P<name>\w+)"')

    def __init__(self, path):
        table_json = self._get_table_json(path)
        self.hidden = table_json.get("isHidden") or table_json.get("isPrivate")
        self.name = table_json['name']
        partitions = table_json['partitions']
        self.source = self._proc_source(partitions)
        self.relations = table_json['relationships']
        self.columns = []
        self.calc_cols = Folder('columns')
        if os.path.isdir(os.path.join(path,'columns')):
            self._proc_columns(os.path.join(path,'columns'))
        self.measures = []
        self.tree = Folder('root')
        if os.path.isdir(os.path.join(path,'measures')):
            self._proc_measures(os.path.join(path,'measures'))


    def _get_table_json(self, path):
        files = [f for f in os.listdir(path) if f[-5:] == '.json']
        if len(files) == 0:
            raise ValueError('Table json not found')
        if len(files) > 1:
            raise ValueError('Ambiguous table json :'+ str(files))
        table_json = os.path.join(path,files[0])
        with open(table_json, 'r') as f:
            return json.load(f)

    def _check_partitions(self, path):
        if os.path.isdir(os.path.join(path, 'partitions')):
            files = os.listdir(os.path.join(path, 'partitions'))
            if len(files) > 0:
                 with open(os.path.join(path, 'partitions', files[0]), 'r') as f:
                    return json.load(f), True
        return None, False

    def _proc_source(self, partitions):
        try:
            source = _proc_expression(partitions[0]['expression'])
        except:
            logging.warning(f'Could not extract source for {self.name}')
            source = None
        if source is not None:
            source = self._source_pat.search(source)
        if source is not None:
            return Tb_name(source['schema'], source['name'])
        else:
            return 'Manual'


    def _proc_columns(self, path):
        for f in os.listdir(path):
            with open(os.path.join(path, f), 'r') as fp:
                c = Table_item(json.load(fp), Table_item.Type.COLUMN, self.name)
                if c.dax is not None:
                    self.calc_cols.add(c, [])
                else:
                    self.columns.append(c)


    def _proc_measures(self, path):
        for f in os.listdir(path):
            with open(os.path.join(path, f), 'r') as fp:
                body = json.load(fp)
                m = Table_item(body, Table_item.Type.MEASURE, self.name)
                self.measures.append(m)
                if 'displayFolder' in body:
                    self.tree.add(m, body['displayFolder'].split('\\'))
                else:
                    self.tree.add(m, [])



