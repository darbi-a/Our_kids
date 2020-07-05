# -*- coding: utf-8 -*-
{
    'name': "Stock Products Slow Move",
    'summary': """Get Not Sold Products """,
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    "version": "12.0.1.0.0",
    "category": "stock",
    "depends": ["purchase_stock", "stock", "sale_management", "product_season", "import_product_variant"],
    "data": [
        "wizard/stock_product_slow_move.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
}
