# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime , date ,timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime as fieldsDatetime
import calendar
from odoo import http
from odoo.http import request
from odoo import tools

import logging

LOGGER = logging.getLogger(__name__)


class pos_order(models.Model):
    _inherit = 'pos.order'

    barcode = fields.Char(string='Barcode')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(pos_order, self)._order_fields(ui_order)

        if ui_order.get('barcode', False):
            order_fields.update({
                'barcode': ui_order['barcode']
            })

        return order_fields


    def return_new_order(self):
        lines = []
        for ln in self.lines:
            lines.append(ln.id)


        vals = {
            'amount_total': self.amount_total,
            'date_order': self.date_order,
            'id': self.id,
            'name': self.name,
            'partner_id': [self.partner_id.id, self.partner_id.name],
            'pos_reference': self.pos_reference,
            'state': self.state,
            'session_id': [self.session_id.id, self.session_id.name],
            'company_id': [self.company_id.id, self.company_id.name],
            'lines': lines,
            'barcode': self.barcode,
        }
        return vals

    def return_new_order_line(self):

        orderlines = self.env['pos.order.line'].search([('order_id.id', '=', self.id)])

        final_lines = []

        for l in orderlines:
            vals1 = {
                'discount': l.discount,
                'id': l.id,
                'order_id': [l.order_id.id, l.order_id.name],
                'price_unit': l.price_unit,
                'product_id': [l.product_id.id, l.product_id.name],
                'qty': l.qty,
                'pack_lot_ids': [p.id for p in l.pack_lot_ids],
            }

            final_lines.append(vals1)
        return final_lines

    def new_pack_lot_lines(self):
        final_lines = []
        orderlines = self.env['pos.order.line'].search([('order_id.id', '=', self.id)])

        for o_line in orderlines:
            for lot_line in o_line.pack_lot_ids:
                vals1 = {
                    'pos_order_line_id': lot_line.pos_order_line_id.id,
                    'id': lot_line.id,
                    'lot_name': lot_line.lot_name,
                }

                final_lines.append(vals1)

        return final_lines

    @api.multi
    def print_pos_report(self):
        return self.env['report'].get_action(self, 'point_of_sale.report_receipt')

    @api.multi
    def print_pos_receipt(self):
        output = []
        discount = 0
        order_id = self.search([('id', '=', self.id)], limit=1)
        orderlines = self.env['pos.order.line'].search([('order_id', '=', order_id.id)])
        payments = self.env['account.bank.statement.line'].search([('pos_statement_id', '=', order_id.id)])
        paymentlines = []
        change = 0
        for payment in payments:
            if payment.amount > 0:
                temp = {
                    'amount': payment.amount,
                    'name': payment.journal_id.name
                }
                paymentlines.append(temp)
            else:
                change += payment.amount

        sub_total_before_discount = 0
        global_discount_percent = 0
        global_discount = 0
        total_without_discount = 0
        for orderline in orderlines:

            new_vals = {
                'product_id': orderline.product_id.display_name,
                'qty': orderline.qty,
                'price_unit': orderline.price_unit,
                'discount': orderline.discount,
                }
            sub_total_before_discount += orderline.price_unit * orderline.qty
            if orderline.price_unit * order_id.amount_total < 0:
                global_discount = abs(orderline.price_unit * orderline.qty)
            else:
                total_without_discount += orderline.price_subtotal_incl
            discount += (orderline.price_unit * orderline.qty * orderline.discount) / 100
            output.append(new_vals)
        if global_discount and total_without_discount:
            global_discount_percent = 100*global_discount/total_without_discount


        return [output, discount, paymentlines, change, sub_total_before_discount,global_discount_percent]


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    order_line_id = fields.Many2one(comodel_name="pos.order.line")
    return_line_ids = fields.One2many(comodel_name="pos.order.line", inverse_name="order_line_id")
    return_qty = fields.Float(compute='compute_return_qty')

    @api.multi
    @api.depends('return_line_ids', 'return_line_ids.qty')
    def compute_return_qty(self):
        for rec in self:
            quantities = rec.return_line_ids.mapped('qty')
            rec.return_qty = sum(abs(q) for q in quantities)
