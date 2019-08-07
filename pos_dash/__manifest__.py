# -*- coding: utf-8 -*-
{
    'name': "pos dashboard",

    'summary': """
        New Dashboard for point of sale """,

    'description': """
        New Dashboard for point of sale  
    """,

    'author': "Islam Abdelmaaboud",
    'website': "http://www.itss-c.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point of sale',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
