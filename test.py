import gen_doc
import json
from string import Template

import render_relations as rl

tables = gen_doc.tables_dict('../template/tables')
views = gen_doc.views_dict('../lcba.databricks.views')
viewtp = Template(open('templates/view.md', 'r').read())
gen_doc.gen_views(views, '', '../temp', viewtp)
templates = {
    'table': Template(open('templates/table.md', 'r').read()),
    'measure': Template(open('templates/measure.md', 'r').read()),
    'column': Template(open('templates/column.md', 'r').read()),
    'relation': Template(open('templates/relation.md', 'r').read())
}
gen_doc.gen_tables(tables, views, '../temp/tables', templates, '../temp/media/')

# relations = tables['Transportation Costs'].relations
# rl.render_relations(relations, 'Transportation Costs', '../temp/media/')