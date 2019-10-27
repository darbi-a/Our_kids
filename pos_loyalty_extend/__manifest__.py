# -*- coding: utf-8 -*-
{
    'name': "Pos Loyalty Extend",

    'summary': """
        Pos Loyalty Extend """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'point of sale',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','pos_loyalty'],

    # always loaded
    'data': [
        'views/loyalty_program.xml',
        'views/templates.xml',
    ],



}