# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'POS All Lines Discounts',
    'version': '1.0',
    'category': 'Point of Sale',
    'author': 'Ahmed Amen',
    'sequence': 6,
    'summary': 'Simple Discounts in the Point of Sale ',
    'description': """

This module allows the cashier to quickly give a percentage
sale discount to all pos order lines.

""",
    'depends': ['point_of_sale'],
    'data': [
        # 'views/pos_discount_views.xml',
        'views/pos_discount_templates.xml'
    ],
    'qweb': [
        'static/src/xml/discount_all.xml',
    ],
    'installable': True,
}
