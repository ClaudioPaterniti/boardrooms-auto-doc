import re
import logging
from collections import namedtuple


class View:

    _name_pat = re.compile(r'view\s+(?P<source>(?:\w+dltdb)|(?:default))\.(?P<name>\w+)\s', re.IGNORECASE)
    _source_pat = re.compile(r'\s(\w+dltdb|default)\.(\w+)\s')
    tb_name = namedtuple('tb_name', ['schema', 'table'])

    def __init__(self, query, filename):
        self.filename = filename
        self.query = query
        self.name = self._parse_name()
        self.sources = self._parse_sources()

    def _parse_name(self):
        name = self._name_pat.search(self.query)
        if name is None:
            logging.error(f'Could not extract view name and source for {self.filename}')
            return ('Unknown', self.filename)
        return self.tb_name(name['source'], name['name'])

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