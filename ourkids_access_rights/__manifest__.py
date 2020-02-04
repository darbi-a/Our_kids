# -*- coding: utf-8 -*-
{
    'name': "Our kids Access Rights",

    'summary': """
        Our kids Access Rights """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'security',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['product','stock','point_of_sale','stock_barcode','stock_cost'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/inventory_valuation.xml',
        'views/stock_picking.xml',
        'views/pos_config.xml',
        'views/templates.xml',
        'views/product_product.xml',
        'views/account_move.xml',

    ],

    'qweb': [
        'static/src/xml/qweb_templates.xml',
    ],
}
