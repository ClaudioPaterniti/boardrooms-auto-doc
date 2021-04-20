import os
from string import Template

from views_pages import *

def gen_views(views, in_path, out_path, template):
    for view in sorted(views):
        create_view_page(views[view], views, template, out_path)