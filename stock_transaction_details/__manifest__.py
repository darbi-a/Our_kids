# -*- coding: utf-8 -*-
{
    'name': "Vendor Transactions Details ",
    'summary': """Vendor Transactions Details """,
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    "version": "12.0.1.0.0",
    "category": "stock",
    "depends": ["purchase_stock", "stock", "sale_management", "product_season", "import_product_variant", "vendor_payments_report"],
    "data": [
        "wizard/wizard_vendor_transactions_details.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
}
