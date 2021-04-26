import graphviz as gv
import html
import re

_table_temp = '<<table border="2" cellborder="1" cellspacing="0">\n$content\n</table>>'
_column_temp = '<tr><td port="c$p" bgcolor="$c" align="left">$text</td></tr>'

def _column(i, text):
    c = _column_temp.replace('$p', str(i))
    c = c.replace('$c', 'grey' if i%2 else 'white')
    c = c.replace('$text', text)
    return c

def _table(name, columns):
    content = []
    content.append(_column(0, f'<b>{html.escape(name)}</b>'))
    for i, c in enumerate(columns):
        content.append(_column(i+1, html.escape(c)))
    table = _table_temp.replace('$content', '\n'.join(content))
    return table

def _proc_relations(relations):
    tables = {}
    for r in relations:
        if r['fromTable'] not in tables:
            tables[r['fromTable']] = []
        tables[r['fromTable']].append(r['fromColumn'])
        if r['toTable'] not in tables:
            tables[r['toTable']] = []
        tables[r['toTable']].append(r['toColumn'])
    tables = {k: sorted(set(i)) for k,i in tables.items()}
    edges = []
    for r in relations:
        from_port = tables[r['toTable']].index(r['toColumn'])+1
        to_port = tables[r['fromTable']].index(r['fromColumn'])+1
        edges.append({
            'tail_name': f'{r["toTable"]}:c{from_port}',
            'head_name': f'{r["fromTable"]}:c{to_port}',
            'style': 'solid' if r['isActive'] else 'dashed',
        })
    return tables, edges

def render_relations(relations, name, path):
    filename = re.sub(r'\W', '', name)
    g = gv.Digraph(name=name, filename=filename, directory=path)
    g.attr('graph', size="6", pad="0", nodesep="0.5", ranksep="0.4", dpi="1080")
    g.attr('node', shape="plaintext", fontsize="8")
    tables, edges = _proc_relations(relations)
    for t, c in tables.items():
        label = _table(t, c)
        g.node(t, label=label)
    for e in edges:
        g.edge(**e)
    g = g.unflatten(stagger=2)
    g.render(cleanup=True, format='png')
    return filename+'.png', len(tables)
