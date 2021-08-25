from code.view import View


def _sources_block(view, views_dict):
    block = ''
    for source in sorted(view.sources):
        block += f'### {source}\n'
        for name in sorted(view.sources[source]):
            key = (source.lower(), name.lower())
            if  key in views_dict:
                name = views_dict[key].name.table
                block += f'- [{name}](./{views_dict[key].page_name})\n'
            else:
                 block += f'- {name}\n'
    return block

def create_view_page(view, views_dict, template):
    source_block = _sources_block(view, views_dict)
    replace_dict = {
        'name': view.name.table,
        'sources': source_block,
        'code': view.query
    }
    return template.substitute(replace_dict)