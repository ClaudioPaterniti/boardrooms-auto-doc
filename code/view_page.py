from code.view import View
from code.utils import escape, encode_special_chars

def _sources_block(view, views_dict):
    block = ''
    for source in sorted(view.sources):
        header = f'### {source}\n'
        content = ''
        for name in sorted(view.sources[source]):
            key = (source.lower(), name.lower())
            if  key in views_dict:
                name = views_dict[key].name.table
                content += f'- [{name}](./{views_dict[key].page_name})\n'
            else:
                 content += f'- {name}\n'
        block += header + escape(content)
    return block

def create_view_page(view, views_dict, template):
    source_block = _sources_block(view, views_dict)
    replace_dict = {
        'name': escape(view.name.table),
        'sources': source_block,
        'code': encode_special_chars(view.query)
    }
    return template.substitute(replace_dict)