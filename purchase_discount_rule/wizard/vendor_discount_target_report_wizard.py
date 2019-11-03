# -*- coding: utf-8 -*-
"""Vendor Discount Target Report Wizard"""

import time

from odoo import api, fields, models


class VendorDiscountTargetReport(models.TransientModel):
    """Vendor Discount Target Report Wizard

    Print discount targets with discounted values for category(ies) of products for vendor(s).
    """
    _name = 'vendor.discount.target.report.wizard'
    _description = 'Vendor Discount Target Report Wizard'

    category_ids = fields.Many2many(
        comodel_name="product.category",
        string="Products Categories",
        required=True,
    )
    date_from = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To', required=True, default=lambda *a: time.strftime('%Y-%m-28'))

    @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['vendor'] = self.env.context.get('active_ids', [])
        data = {
            'ids': data['vendor'],
            'model': 'res.partner',
            'form': data
        }
        return self.env.ref('purchase_discount_rule.report_vendor_discount_target_action'). \
               report_action(docids=data['ids'], data=data)
