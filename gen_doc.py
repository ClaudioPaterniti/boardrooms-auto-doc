import os
from string import Template
import argparse
import json
import re

from view import View
import views_page as vp
from table import Table
import table_page as tp


def views_dict(path, ext='.sql'):
    views = {}
    for file in os.listdir(path):
        if file[-4:] == ext:
            with open(os.path.join(path,file), 'r') as f:
                v = View(f.read(), file[:-4])
                views[(v.name[0].lower(), v.name[1].lower())] = v
    return views

def tables_dict(path, include_hidden = False):
    tables = {}
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    for dir in dirs:
        t = Table(dir)
        if include_hidden or not t.hidden:
            tables[t.name] = t
    return tables

def gen_views(views, out_path, template):
    for view in sorted(views):
        page = vp.create_view_page(views[view], views, template)
        with open(os.path.join(out_path, views[view].name[1]+'.md'), 'w') as fo:
            fo.write(page)

def gen_tables(tables, views, out_path, templates, media_path):
    measures = []
    for _, t in tables.items():
        measures.extend([m.name for m in t.measures])
    for table in sorted(tables):
        page = tp.create_table_page(tables[table], measures, views, templates, media_path)
        filename = re.sub(r'\W', '', tables[table].name)
        with open(os.path.join(out_path, filename+'.md'), 'w') as fo:
            fo.write(page)

if __name__ == '__main__':
    with open('refs.json', 'r') as fp:
        refs = json.load(fp)
    views_path = refs['notebooks_path']
    tables_path = refs['model_path']
    wiki_path = refs['wiki_path']
    wiki_media = refs['wiki_media']
    views = views_dict(views_path)
    tables = tables_dict(tables_path)
    templates = {}
    for template in os.listdir('./templates'):
        with open(os.path.join('templates', template)) as fp:
            templates[template[:-3]] = Template(fp.read())
    out = {
        'views': os.path.join(wiki_path, 'views'),
        'model': os.path.join(wiki_path, 'model'),
        'media': os.path.join(wiki_media, 'model')
    }
    for _, p in out.items():
        if not os.path.isdir(p):
            os.mkdir(p)
    gen_views(views, out['views'], templates['view'])
    gen_tables(tables, views, out['model'] , templates, out['media'])
