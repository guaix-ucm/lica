# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# --------------------

import jinja2


def render_from(package, template, context):
    return jinja2.Environment(
        loader=jinja2.PackageLoader(package, package_path='templates')
    ).get_template(template).render(context)
