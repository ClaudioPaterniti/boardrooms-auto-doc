import os
import re
import logging

from code.table import Table

_render_relations = False
try:
    import code.render_relations as render
    _render_relations = True
except ImportError as e:
    logging.warning(f'Install Graphviz for visual rendering of relations:\n{e}')


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
        deps = ', '.join(sorted(deps))
        rd = {
            'name': m.name,
            'format': m.format,
            'code': m.dax,
            'deps': deps
        }
        blocks.append(template.substitute(rd))
    return '\n'.join(blocks)


def _relations_block(table, tables, template, media_path, render_relations):
    if len(table.relations) == 0:
        return ''
    relations = table.relations.copy()
    done = {table.name}; to_do = relations.copy()
    while to_do:
        r = to_do.pop()
        if r['toTable'] not in done:
            t = tables[r['toTable']]
            relations.extend(t.relations)
            to_do.extend(t.relations)
            done.add(r['toTable'])
    if render_relations:
        try:
            logging.info(f'Rendering relations')
            img, n = render.render_relations(relations, table.name, media_path)
            link = f'/docs/.media/model/{img}'
            size = min(950, 100*n)
            return f'![Image Error]({link} ={size}x)'
        except Exception as e:
            logging.error(f'Could not render relations:\n{e}')
    blocks = []
    for r in relations:
        r['link'] = re.sub(r'\W', '', r['toTable'])
        blocks.append(template.substitute(r))
    return '\n'.join(blocks)


def create_table_page(table, tables, measures_list, views, templates, media_path, visual_relations = True):
    global _render_relations
    render_relations = _render_relations and visual_relations
    columns = _columns_block(table, templates['column'])
    measures = _measures_block(table.measures, measures_list, templates['measure'])
    cols = {c.name for c in table.columns}
    calculated = _measures_block(table.calc_cols, cols, templates['measure'])
    relations = _relations_block(table, tables, templates['relation'], media_path, render_relations)
    source = table.source
    if table.source != 'Manual':
        try:
            source = views[(table.source[0].lower(), table.source[1].lower())].name[1]
        except KeyError:
            logging.warning(f'Source view {table.source} for table {table.name} not found')
            source = table.source[1]
    replace_dict = {
        'name': table.name,
        'source': source,
        'columns': columns,
        'calculated': calculated,
        'measures': measures,
        'relations': relations
    }
    return templates['table'].substitute(replace_dict)