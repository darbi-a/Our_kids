# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID

import logging

LOGGER = logging.getLogger(__name__)


class Invoice(models.Model):
    _inherit = 'account.invoice.line'

    last_purchase_price = fields.Float(compute="_compute_last_purchase_price")
    invoice_type = fields.Selection(related='invoice_id.type')

    @api.depends('invoice_id.partner_id', 'product_id')
    @api.multi
    def _compute_last_purchase_price(self):
        for line in self:
            if line.invoice_id.partner_id and line.product_id:
                last_price = self.env['account.invoice.line'].search_read(
                   domain=[('invoice_id.partner_id', '=', line.partner_id.id),
                           ('product_id', '=', line.product_id.id),
                           ('invoice_id.state', 'in', ['open', 'paid'])],
                   fields=['price_unit'],
                   limit=1, order='create_date')
                if last_price:
                    line.last_purchase_price = last_price[0]['price_unit']

    @api.onchange('last_purchase_price')
    def _onchange_last_purchase_price(self):
        for line in self:
            if line.last_purchase_price and line.invoice_id.type == 'in_refund':
                line.price_unit = line.last_purchase_price
