import os

from view import View

def views_dict(path, ext='.sql'):
    views = {}
    for file in os.listdir(path):
        print(f'Processing {file}')
        if file[-4:] == ext:
            with open(os.path.join(path,file), 'r') as f:
                v = View(f.read())
                views[(v.name[0].lower(), v.name[1].lower())] = v
    return views

def create_view_sources_block(view, views_dict):
    block = ''
    for source in sorted(view.sources):
        block += f'### {source}\n'
        for name in sorted(view.sources[source]):
            key = (source.lower(), name.lower())
            if  key in views_dict:
                name = views_dict[key].name[1]
                block += f'- [{name}](./{name}.md)\n'
            else:
                 block += f'- {name}\n'
    return block

def create_view_page(view, views_dict, template, path):
    source_block = create_view_sources_block(view, views_dict)
    replace_dict = {
        'overview': '',
        'title': view.name[1],
        'sources': source_block,
        'code': view.query
    }
    with open(os.path.join(path, view.name[1]+'.md'), 'w') as fo:
        fo.write(template.substitute(replace_dict))
