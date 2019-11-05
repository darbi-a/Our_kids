# -*- coding: utf-8 -*-
{
    'name': "Purchase Discount Rules",
    'summary': """Apply Discount On PO Lines With Rules""",
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    "version": "11.0.1.0.0",
    "category": "Purchase Management",
    "depends": ["purchase","purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_reports.xml",
        "views/report_vendor_discount_target.xml",
        "views/report_purchase_order.xml",
        "wizard/purchase_order_global_discount_wizard.xml",
        "wizard/vendor_discount_target_report_wizard.xml",
        "views/purchase_order_views.xml",
        "views/purchase_discount_rule.xml",

    ],
    "license": 'AGPL-3',
    'installable': True,
}
