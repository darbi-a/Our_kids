# -*- coding: utf-8 -*-
{
    'name': 'POS Speed Up',
    'version': '12.0.1',
    'category': 'Point Of Sale',
    'author': 'D.Jane',
    'sequence': 10,
    'summary': 'Boosts Odoo POS loading speed 1000-times faster',
    'description': "",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/header.xml',
        'views/clear_pos_data.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'qweb': ['static/src/xml/loading.xml'],
    'installable': True,
    'application': True,
    'price': 199,
    'license': 'OPL-1',
    'currency': 'EUR',
}
