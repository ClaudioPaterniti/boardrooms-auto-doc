import os
from string import Template

from view import View
import views_page as vp
from table import Table
import table_page as tp

def not_verb(*args, **kwargs):
    pass
    
verb = print

def views_dict(path, ext='.sql'):
    views = {}
    for file in os.listdir(path):
        verb(f'Processing view {file}')
        if file[-4:] == ext:
            with open(os.path.join(path,file), 'r') as f:
                v = View(f.read())
                views[(v.name[0].lower(), v.name[1].lower())] = v
    return views

def tables_dict(path, include_hidden = False):
    tables = {}
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    for dir in dirs:
        verb(f'Processing table dir {dir}')
        t = Table(dir)
        if include_hidden or not t.hidden:
            tables[t.name] = t
    return tables

def gen_views(views, in_path, out_path, template):
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
        with open(os.path.join(out_path, tables[table].name+'.md'), 'w') as fo:
            fo.write(page)
    