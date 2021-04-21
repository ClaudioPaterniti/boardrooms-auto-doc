import re

from table import Table

def _columns_block(table, template):
    blocks = []
    for c in table.columns:
        rd = {
            'name': c.name,
            'source': c.source,
            'type': c.data_type,
            'format': c.format
        }
        blocks.append(template.substitute(rd))
    return '\n'.join(blocks)

def _measures_block(table, measures, template):
    blocks = []
    for m in table.measures:
        deps = re.findall(r'\[+?\]', m.dax)
        deps = {d for d in deps if d in measures}
        deps = ', '.join(deps)
        rd = {
            'name': m.name,
            'format': m.format,
            'code': m.dax,
            'deps': deps
        }
        blocks.append(template.substitute(rd))
    return '\n'.join(blocks)

def _relations_block(table, template):
    blocks = []
    for r in table.relations:
        rd = r.copy()
        if rd['crossFilteringBehavior']:
            rd['crossFilteringBehavior'] = '<|'
        blocks.append(template.substitute(rd))
    return '\n'.join(blocks)

def create_table_page(table, measures, views, templates):
    columns = _columns_block(table, templates['column'])
    measures = _measures_block(table, measures, templates['measure'])
    columns_from =  [r['fromColumn'] for r in table.relations]
    columns_from = '\n'.join(columns_from)
    relations = _relations_block(table, templates['relation'])
    source = table.source
    if table.source != 'Manual':
        source = views[table.source[0].lower(), table.source[1].lower()].name[1]
    replace_dict = {
        'name': table.name,
        'overview': '',
        'source': source,
        'columns': columns,
        'measures': measures,
        'columns_from': columns_from,
        'relations': relations
    }
    return templates['table'].substitute(replace_dict)