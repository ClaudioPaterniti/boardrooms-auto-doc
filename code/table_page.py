import os
import re
import logging

from code.table import Table

_render_relations = False
try:
    import code.render_relations as render
    _render_relations = True
except ImportError as e:
    logging.warning(f'Install Graphviz for visual rendering of relations:\n{e}\n')


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

def _measures_block(tree, measures, template, folder_template):
    blocks = []
    for name, folder in tree.folders.items():
        rd = {
            'name': name,
            'measures': _measures_block(folder, measures, template, folder_template)
        }
        blocks.append(folder_template.substitute(rd))
    for m in tree.measures:
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
    s = '\n'.join(blocks)
    if tree.level > 0:
        s = re.sub(r'^', '>', s, flags=re.MULTILINE)
    return s


def _relations_block(table, tables, template, media_path, render_relations):
    if len(table.relations) == 0:
        return ''
    relations = table.relations.copy()
    done = {table.name}; to_do = relations.copy()
    while to_do:
        r = to_do.pop()
        if r['toTable'] not in done:
            try:
                t = tables[r['toTable']]
                relations.extend(t.relations)
                to_do.extend(t.relations)
            except KeyError as e:
                logging.error(f"Table {r['toTable']} related to {table.name} not found")
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
    render_relations = _render_relations and visual_relations
    columns = _columns_block(table, templates['column'])
    measures = _measures_block(table.tree, measures_list, templates['measure'], templates['folder'])
    cols = {c.name for c in table.columns}
    calculated = _measures_block(table.calc_cols, cols, templates['measure'], templates['folder'])
    relations = _relations_block(table, tables, templates['relation'], media_path, render_relations)
    source = table.source
    if table.source != 'Manual':
        key = (table.source.schema.lower(), table.source.table.lower())
        if key in views:
            source = views[key].name.table
            source_link = re.sub(r'\W', '', source)
            source = f'[{source}](../Databricks-Objects/{source_link}.md)'
        else:
            if views:
                logging.warning(f'Source view {table.source} for table {table.name} not found')
            source = table.source.table
    replace_dict = {
        'name': table.name,
        'source': source,
        'columns': columns,
        'calculated': calculated,
        'measures': measures,
        'relations': relations
    }
    return templates['table'].substitute(replace_dict)