import os
from string import Template
import argparse
import json
import re

from code.view import View
import code.view_page as vp
from code.table import Table
import code.table_page as tp

_section_pat = re.compile(r'(#+.+?$)((?:[^#]|(?:\\#))*)', flags=re.MULTILINE | re.DOTALL)

def views_dict(path, ext='.sql'):
    views = {}
    for file in os.listdir(path):
        if file[-4:] == ext:
            with open(os.path.join(path,file), 'r') as f:
                v = View(f.read(), file[:-4])
                views[(v.name.schema.lower(), v.name.table.lower())] = v
    return views

def tables_dict(path, include_hidden = False):
    tables = {}
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    for dir in dirs:
        t = Table(dir)
        if include_hidden or not t.hidden:
            tables[t.name] = t
    return tables

def get_sections_tree(page):
    sections = _section_pat.findall(page)
    parents = ['']*6
    tree = []
    for name, content in sections:
        level = name.count('#')
        parents[level-1] = name
        tree.append(('/'.join(parents[:level]), name+content))
    return tree

def merge_page(old, new):
    old_tree = get_sections_tree(old)
    new_tree = dict(get_sections_tree(new))
    page = []
    for section, content in old_tree:
        if section in new_tree:
            page.append(new_tree[section])
        else:
            page.append(content)
    return ''.join(page)


def gen_views(views, out_path, template, merge):
    for view in sorted(views):
        page = vp.create_view_page(views[view], views, template)
        filename = views[view].name.table+'.md'
        out_file = os.path.join(out_path, filename)
        if merge and os.path.isfile(out_file):
            with open(out_file, 'r') as fp:
                old = fp.read()
            page = merge_page(old, page)
        with open(out_file, 'w') as fo:
            fo.write(page)


def gen_tables(tables, views, out_path, templates, media_path, visual, merge):
    measures = set()
    for _, t in tables.items():
        measures.update({m.name for m in t.measures})
    for table in sorted(tables):
        page = tp.create_table_page(tables[table], tables, measures, views, templates, media_path, visual)
        filename = re.sub(r'\W', '', tables[table].name)+'.md'
        out_file = os.path.join(out_path, filename)
        if merge and os.path.exists(out_file):
            with open(out_file, 'r') as fp:
                old = fp.read()
            page = merge_page(old, page)
        with open(out_file, 'w') as fo:
            fo.write(page)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refs', type= str, default='./default_refs.json')
    parser.add_argument('--no-visual', action='store_true')
    parser.add_argument('--no-merge', action ='store_true')
    args = parser.parse_args()

    refs = args.refs
    if not os.path.isfile(refs):
        if not os.path.isfile(refs+'.json'):
            raise FileNotFoundError(f'Ref file: {args.refs} not found')
        refs = refs+'.json'
    with open(refs, 'r') as fp:
        refs = json.load(fp)
    views = views_dict(refs['notebooks_path'])
    tables = tables_dict(refs['model_path'])
    templates = {}
    for template in os.listdir('./templates'):
        with open(os.path.join('templates', template)) as fp:
            templates[template[:-3]] = Template(fp.read())
    out = {
        'views': os.path.join(refs['wiki_path'], 'Wiki', 'views',),
        'model': os.path.join(refs['wiki_path'], 'Wiki', 'model',),
        'media': os.path.join(refs['wiki_path'], '.media', 'model',)
    }
    for _, p in out.items():
        if not os.path.isdir(p):
            os.makedirs(p)
    gen_views(views, out['views'], templates['view'], not args.no_merge)
    gen_tables(tables, views, out['model'] , templates, out['media'], not args.no_visual, not args.no_merge)
