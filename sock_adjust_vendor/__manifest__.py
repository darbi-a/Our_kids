# -*- coding: utf-8 -*-
{
    'name': "Inventory Adjustment by Vendors",

    'summary': """
        Inventory Adjustment by Vendors """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'stock',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['stock','import_product_variant','adjustment_difference_qty'],

    # always loaded
    'data': [
        'views/stock_inventory.xml',
    ],



}