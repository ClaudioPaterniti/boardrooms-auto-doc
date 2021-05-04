import re
import logging
from collections import namedtuple

Tb_name = namedtuple('Tb_name', ['schema', 'table'])

class View:

    _name_pat = re.compile(r'view\s+(?P<source>(?:\w+dltdb)|(?:default))\.(?P<name>\w+)\s', re.IGNORECASE)
    _source_pat = re.compile(r'\s(\w+dltdb|default)\.(\w+)\s')
    _notebook_name_pat = re.compile(r'\d*\.\s*(?P<name>\S.*)')

    def __init__(self, query, filename):
        self.filename = filename
        note_name = self._notebook_name_pat.search(filename)
        self.notebook = filename if note_name is None else note_name['name']
        self.query = query
        self.name = self._parse_name()
        self.sources = self._parse_sources()

    def _parse_name(self):
        name = self._name_pat.search(self.query)
        if name is None:
            logging.error(f'Could not extract view name and db for {self.filename}')
            return Tb_name('Unknown', self.notebook)
        return Tb_name(name['source'], name['name'])

    def _parse_sources(self):
        items = self._source_pat.findall(self.query)
        sources = {}
        for source, name in items:
            if (source,name) != self.name:
                if source in sources:
                    sources[source].add(name)
                else:
                    sources[source] = {name}
        return sources