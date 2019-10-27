# -*- coding: utf-8 -*-
{
    'name': "Pos Money Out",

    'summary': """
        Pos Money Out """,

    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'Point Of Sale',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/money_out_type.xml',
        'views/pos_box_out.xml',
        'views/pos_session.xml',
    ],



}