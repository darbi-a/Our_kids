# -*- coding: utf-8 -*-
{
    'name': "Product Card Report",
    'summary': """Product Card Report""",
    'author': "Mahmoud Naguib, ITSS <https://www.itss-c.com>",
    "version": "11.0.1.0.0",
    "category": "stock",
    "depends": ["stock"],
    "data": [

        'wizard/product_card_report.xml',
        'views/stock_picking.xml',
        'views/product_product.xml',
        'views/product_card_templates.xml',

    ],
    "license": 'AGPL-3',
    'installable': True,
}
