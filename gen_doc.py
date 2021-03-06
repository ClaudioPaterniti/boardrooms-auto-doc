import os
import traceback
import argparse
import json
import re
import logging
import pathlib
from string import Template

from code.view import View
import code.view_page as vp
from code.TE_model_parser import Table
import code.table_page as tp
from code.utils import escape_filename, decode_special_chars, encode_special_chars

_section_pat = re.compile(r'(^\s*#+.+?$)((?:[^#])*)', flags=re.MULTILINE | re.DOTALL)
_code_block = re.compile(r'(```.*?```)', flags=re.MULTILINE | re.DOTALL)
_file_pat = re.compile(r'(?P<name>.+)(?P<ext>\.[^\.]*$)')

def views_dict(path, ext):
    views = {}
    for file in os.listdir(path):
        file_name = _file_pat.search(file)
        if  re.fullmatch(ext, file_name['ext']) is not None:
            logging.info(f'Parsing view: {file}')
            with open(os.path.join(path,file), 'r') as f:
                v = View(f.read(), file_name['name'], escape_filename(file_name['name'])+'.md')
                views[(v.name.schema.lower(), v.name.table.lower())] = v
    return views

def tables_dict(path, include_hidden = False):
    tables = {}
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    for dir in dirs:
        logging.info(f'Parsing table: {pathlib.PurePath(dir).name}')
        try:
            t = Table(dir)
            if include_hidden or not t.hidden:
                tables[t.name] = t
        except Exception as e:
            logging.error(f'Parsing failed:\n')
            traceback.print_exc()
    return tables

def escape_code_blocks(page):
    blocks = _code_block.split(page)
    for i in range(1,len(blocks),2):
        blocks[i] = encode_special_chars(blocks[i])
    return ''.join(blocks)

def get_sections_tree(page):
    sections = _section_pat.findall(page)
    parents = ['']*6
    tree = []; toc = ''
    for name, content in sections:
        level = name.count('#')
        parents[level-1] = name
        full_path = '/'.join(parents[:level])
        if '[[_TOC_]]' in content:
            toc = full_path
        tree.append((full_path, name+content))
    return tree, toc

def merge_page(old, new):
    old_tree, old_toc = get_sections_tree(escape_code_blocks(old))
    new_chaps, new_toc = get_sections_tree(new)
    new_tree = dict(new_chaps)
    if old_toc != new_toc:
        new_tree[new_toc] = new_tree[new_toc].replace('[[_TOC_]]', '')
    page = []
    for section, content in old_tree:
        if section in new_tree:
            page.append(new_tree[section])
        else:
            page.append(content)
    return ''.join(page)


def gen_views(views, out_path, template, merge):
    for view in sorted(views):
        #filename = re.sub(r'\W', '', views[view].name.table)+'.md'
        filename = views[view].page_name
        logging.info(f'Generating view page {filename}')
        page = vp.create_view_page(views[view], views, template)
        out_file = os.path.join(out_path, filename)
        if merge and os.path.isfile(out_file):
            logging.info(f'Merging with old {filename}')
            with open(out_file, 'r') as fp:
                old = fp.read()
            page = merge_page(old, page)
        with open(out_file, 'w') as fo:
            fo.write(decode_special_chars(page))


def gen_tables(tables, views, out_path, templates, media_path, visual, merge, dpi):
    measures = set()
    for _, t in tables.items():
        measures.update({m.name for m in t.measures})
    for table in sorted(tables):
        filename = escape_filename(tables[table].name)+'.md'
        logging.info(f'Generating table page {filename}')
        page = tp.create_table_page(tables[table], tables, measures, views, templates, media_path, visual, dpi)
        out_file = os.path.join(out_path, filename)
        if merge and os.path.exists(out_file):
            logging.info(f'Merging with old {filename}')
            with open(out_file, 'r') as fp:
                old = fp.read()
            page = merge_page(old, page)
        with open(out_file, 'w') as fo:
            fo.write(decode_special_chars(page))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--refs', '-r', '--profile', '-p', type= str, default='./default_refs.json',
                        help='path to the references file')
    parser.add_argument('--views_ext', type=str, default = '.sql',
                        help='file extensions to parse in the views folder')
    parser.add_argument('--serializer', '-s', type=str, default='te',
                        help='indicate what serializer procued the model, options: te or sloth')
    parser.add_argument('--no-visual', action='store_true',
                        help='disable visual rendering of relations')
    parser.add_argument('-dpi', type= int, default=720,
                        help= 'set relation images resolution')
    parser.add_argument('--no-merge', action ='store_true',
                        help='disable documentation pages merging, it overwrites current pages')
    parser.add_argument('--no-views', action ='store_true',
                        help='disable views pages generation')
    parser.add_argument('--verbose', '-v', type=int, default=3,
                        help='verbosity level')
    args = parser.parse_args()
    
    args.verbose = max(0, min(5, args.verbose))
    logging.basicConfig(format='%(levelname)s: %(message)s', level=50-args.verbose*10)
    refs = args.refs
    if args.serializer == 'sloth':
        from code.sloth_parser import Table
    if not os.path.isfile(refs):
        if not os.path.isfile(refs+'.json'):
            raise FileNotFoundError(f'Ref file: {args.refs} not found')
        refs = refs+'.json'
    with open(refs, 'r') as fp:
        refs = json.load(fp)
    templates = {}
    for template in os.listdir('./templates'):
        with open(os.path.join('templates', template)) as fp:
            templates[template[:-3]] = Template(fp.read())
    out = {
        'model': os.path.join(refs['wiki_path'], 'docs', 'Wiki', 'Resources', 'Power-BI-Model',),
        'media': os.path.join(refs['wiki_path'], 'docs', '.media', 'model',)
    }
    if refs['notebooks_path'] and not args.no_views:
        views = views_dict(refs['notebooks_path'], args.views_ext)
        out['views'] =  os.path.join(refs['wiki_path'], 'docs', 'Wiki', 'Resources', 'Databricks-Objects',)
    else:
        views = {}
    for _, p in out.items():
        if not os.path.isdir(p):
            os.makedirs(p)
    tables = tables_dict(refs['model_path'])
    if views:
        gen_views(views, out['views'], templates['view'], not args.no_merge)
    gen_tables(tables, views, out['model'] , templates, out['media'], not args.no_visual, not args.no_merge, args.dpi)
