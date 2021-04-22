import os
import re
import json
import ast
from enum import Enum


def _proc_expression(exp):
    if isinstance(exp, list):
        exp = exp[1:] if exp[0] == '' else exp
        return '\n'.join(exp)
    else:
        return exp

def _proc_annotations(item):
    if 'annotations' not in item:
        return {}
    annotations = {i['name']: i.get('value') for i in item['annotations']}
    return annotations

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
                print(f'Could not extract format from {self.table} - {self.name}')
                self.format = ''
        self.source = item.get("sourceColumn")


class Table:

    _source_pat = re.compile(r'\s(?P<schema>\w+)_Schema\{\[Name="(?P<name>\w+)"')

    def __init__(self, path):
        table_json = self._get_table_json(path)
        self.hidden = table_json.get("isHidden") or table_json.get("isPrivate")
        self.name = table_json['name']
        part_json, partition = self._check_partitions(path)
        source_json = part_json if partition else table_json
        self.source = self._proc_source(source_json, partition)
        annotations = _proc_annotations(table_json)
        self.relations = self._proc_relations(annotations['TabularEditor_Relationships'])
        self.columns = []
        self.calc_cols = []
        if os.path.isdir(os.path.join(path,'columns')):
            self._proc_columns(os.path.join(path,'columns'))
        self.measures = []
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

    def _proc_source(self, source_json, partition):
        try:
            if partition:
                source = _proc_expression(source_json['source'].get('expression'))
            else:
                source = _proc_expression(source_json['partitions'][0]['source'].get('expression'))
        except:
            print(f'Could not extract source for {self.name}')
            source = None
        if source is not None:
            source = self._source_pat.search(source)
        if source is not None:
            return (source['schema'], source['name'])
        else:
            return 'Manual'


    def _proc_columns(self, path):
        for f in os.listdir(path):
            with open(os.path.join(path, f), 'r') as fp:
                c = Table_item(json.load(fp), Table_item.Type.COLUMN, self.name)
                if c.dax is not None:
                    self.calc_cols.append(c)
                else:
                    self.columns.append(c)


    def _proc_measures(self, path):
        for f in os.listdir(path):
            with open(os.path.join(path, f), 'r') as fp:
                self.measures.append(Table_item(json.load(fp), Table_item.Type.MEASURE, self.name))


    def _proc_relations(self, relations):
        if isinstance(relations, list):
            relations = '\n'.join(relations)
        else:
            return []
        relations = json.loads(relations)
        for r in relations:
            if 'toCardinality' in r:
                r['toCardinality'] = '*'
            else:
                r['toCardinality'] = '1'
            r['crossFilteringBehavior'] = 'crossFilteringBehavior' in r
            r['isActive'] = 'isActive' not in r
        return relations


