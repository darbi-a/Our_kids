# -*- coding: utf-8 -*-
{
    'name': "Stock Products Adjustment",
    'summary': """Get Not Sold Products """,
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    "version": "12.0.1.0.0",
    "category": "stock",
    "depends": ["purchase_stock", "stock", "sale_management", "product_season"],
    "data": [
        "wizard/stock_products_adjustment.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
}
