# -*- coding: utf-8 -*-
{
    'name': "pos Promotions",

    'summary': """
        Pos Promotions """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'point of sale',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/pos_promotions.xml',
        'views/templates.xml',
    ],

    'qweb': [
        'static/src/xml/promotions.xml',
    ],



}