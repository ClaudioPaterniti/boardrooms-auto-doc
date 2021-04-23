import os
import re

from code.table import Table

_render_relations = False
try:
    import code.render_relations as render
    _render_relations = True
except ImportError as e:
    print('Install Graphviz for visual rendering of relations:\n\t',e)


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

def _measures_block(items, measures, template):
    blocks = []
    for m in items:
        if not m.dax:
            continue
        deps = re.findall(r'\[(.+?)\]', m.dax)
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


def _relations_block(table, template, media_path, render_relations):
    if len(table.relations) == 0:
        return ''
    if render_relations:
        try:
            img, n = render.render_relations(table.relations, table.name, media_path)
            link = f'/docs/.media/model/{img}'
            size = min(900, 100*n)
            return f'![Image Error]({link} ={size}x)'
        except Exception as e:
            print(f'Could not render relations for {table.name}:\n\t{e}')
    blocks = []
    for r in table.relations:
        blocks.append(template.substitute(r))
    return '\n'.join(blocks)


def create_table_page(table, measures_list, views, templates, media_path, visual_relations = True):
    global _render_relations
    render_relations = _render_relations and visual_relations
    columns = _columns_block(table, templates['column'])
    measures = _measures_block(table.measures, measures_list, templates['measure'])
    cols = {c.name for c in table.columns}
    calculated = _measures_block(table.calc_cols, cols, templates['measure'])
    relations = _relations_block(table, templates['relation'], media_path, render_relations)
    source = table.source
    if table.source != 'Manual':
        try:
            source = views[(table.source[0].lower(), table.source[1].lower())].name[1]
        except KeyError:
            print(f'Source view {(table.source[0], table.source[1])} for table {table.name} not found')
            source = table.source[1]
    replace_dict = {
        'name': table.name,
        'overview': '',
        'source': source,
        'columns': columns,
        'calculated': calculated,
        'measures': measures,
        'relations': relations
    }
    return templates['table'].substitute(replace_dict)