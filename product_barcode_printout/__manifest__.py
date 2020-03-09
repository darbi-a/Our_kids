# -*- coding: utf-8 -*-
{
    'name': "Product Barcode Print Out",

    'summary': """
        Product Barcode Print Out """,

    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'Product',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['product','purchase'],

    # always loaded
    'data': [
        'wizard/po_barcode_wizard.xml',
        'views/templates.xml',
        'views/templates_first_label.xml',
        'views/purchase_order.xml',

    ],



}