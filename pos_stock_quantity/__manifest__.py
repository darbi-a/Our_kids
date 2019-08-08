# -*- coding: utf-8 -*-
{
    'name': 'POS Available Quantity',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'author': 'A7med Amin',
    'sequence': 10,
    'summary': 'Display Stocks on POS Location. Update Real-Time Quantity Available.',
    'description': "",
    'depends': ['point_of_sale','pos_speed_up'],
    'data': [
        'views/header.xml',
        'views/config.xml'
    ],
    'images': ['static/description/banner.png'],
    'qweb': ['static/src/xml/pos_stock.xml'],
    'installable': True,
    'application': True,
}
