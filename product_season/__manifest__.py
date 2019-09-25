# -*- coding: utf-8 -*-
{
    'name': "Product Season",

    'summary': """
        Product Season """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'product',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['product','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_product.xml',
        'views/product_season.xml',
    ],



}