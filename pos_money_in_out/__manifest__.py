# -*- coding: utf-8 -*-
{
    'name': "POS Money Box LOG",

    'summary': """
        """,

    'description': """
    """,

    'author': "Ahmed Amen",
    'website': "http://www.itss-c.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'POS',
    'version': '12.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_box.xml',
        'views/journal.xml',
        'views/money_log.xml',
        'views/session.xml',
    ],
    # only loaded in demonstration mode

}