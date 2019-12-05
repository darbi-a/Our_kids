# -*- coding: utf-8 -*-
{
    'name': "OurKids Purchase",

    'summary': """
        OurKids Purchase """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'purchase',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['purchase','purchase_stock','import_product_variant'],

    # always loaded
    'data': [
        'views/purchase_order_line.xml',
        'views/purchase_order.xml',
        'views/product_product.xml',
        'views/account_invoice.xml',
        'views/stock_move.xml',
    ],



}