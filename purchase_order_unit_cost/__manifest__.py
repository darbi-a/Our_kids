# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Unit Cost",
    'summary': """Add Unit Cost In Purchase Order Lines""",
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    "version": "12.0.1.0.0",
    "category": "Purchase Management",
    "depends": ["purchase", "stock_cost"],
    "data": [
        "views/purchase_order_views.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
}
