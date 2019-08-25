# -*- coding: utf-8 -*-
"""Purchase Discount Target Report"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseDiscountTargetReport(models.AbstractModel):
    _name = 'report.purchase_discount_rule.report_vendor_discount_target'

    def _get_vendor_targets(self, vendor, data):
        product_targets = []
        date_from = data['date_from']
        date_to = data['date_to']
        products = self.env['product.product'].search([('categ_id', 'in', data['category_ids'])])
        for product in products:
            lines = self.env['purchase.order.line'].search(
                [('order_id.partner_id', '=', vendor.id),
                 ('order_id.date_order', '>=', date_from),
                 ('order_id.date_order', '<=', date_to),
                 ('order_id.state', '=', 'purchase'),
                 ('product_id', '=', product.id)])
            product_qty = sum(line.product_qty for line in lines)
            if product_qty:
                discount_qty = 0
                discount_fixed_amount = 0
                discount_percentage_amount = 0
                for line in lines:
                    discount_qty += line.discount_qty
                    discount_fixed_amount += line.fixed_discount
                    discount_percentage_amount += line.discount * (line.price_unit * line.product_qty) / 100
                target_qty = self.env['purchase.discount.rule.line'].search_read(
                        [('rule_id.vendor_id', '=', vendor.id), ('rule_id.date_from', '>=', date_from),
                         ('rule_id.date_to', '<=', date_to),
                         ('rule_id.state', '=', 'confirmed'), ('product_id', '=',product.id),
                         ('min_value', '>', product_qty)],
                        ['min_value'],
                        order='min_value', limit=1)
                target_qty = target_qty and target_qty[0]['min_value'] - product_qty or 0.0
                product_targets.append({
                    'product': product.name,
                    'product_qty': product_qty,
                    'target_qty': target_qty,
                    'discount_qty': discount_qty,
                    'discount_fixed_amount': discount_fixed_amount,
                    'discount_percentage_amount': discount_percentage_amount,
                })
        return product_targets

    def _get_targets_data(self, vendors, data):
        res = []
        for vendor in vendors:
            res.append({
                'vendor': vendor.name,
                'targets': self._get_vendor_targets(vendor, data),
            })
        return res

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        shifts_report = self.env['ir.actions.report']. \
            _get_report_from_name('purchase_discount_rule.report_vendor_discount_target')
        vendors = self.env['res.partner'].browse(data['ids'])
        return {
            'doc_ids': self.ids,
            'doc_model': shifts_report.model,
            'docs': vendors,
            'dates': [data['form']['date_from'], data['form']['date_to']],
            'get_targets': self._get_targets_data(vendors, data['form']),
        }
