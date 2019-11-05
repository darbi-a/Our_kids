# -*- coding: utf-8 -*-
{
    'name': "Refund For Returned Products",

    'summary': """
        Refund For Returned Products """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['account','stock','point_of_sale'],

    # always loaded
    'data': [
        'views/account_invoice.xml',
        'views/stock_picking_type.xml',
        'views/pos_config.xml',
    ],



}