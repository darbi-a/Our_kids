# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

LOGGER = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_available_pickings(self):
        used_pickings = self.search([]).mapped('return_picking_ids')
        available_pickings = self.env['stock.picking'].search([
            ('id','not in',used_pickings.ids),
            ('picking_type_id.code','=',['outgoing','incoming']),
            ('picking_type_id.use_in_returning','=',True),
            ('state','=','done'),
            # '|',
            ('partner_id','=',self.partner_id.id),
            # ('partner_id','=',False),
        ])
        return available_pickings.ids

    @api.depends('partner_id')
    def compute_available_pickings(self):
        for rec in self:
            rec.available_pickings = rec.get_available_pickings()

    return_picking_ids = fields.Many2many(comodel_name="stock.picking")

    available_pickings = fields.Many2many(comodel_name="stock.picking",compute='compute_available_pickings',defualt= lambda x:x.get_available_pickings())

    @api.onchange('partner_id')
    def onchange_partner_with_return_picknings(self):
        self.update({'return_picking_ids': [(5,)]})

    @api.onchange('return_picking_ids')
    def onchange_return_pickings(self):
        new_invoice_lines = []
        # deleted_invoice_lines = self.env['account.invoice.line']
        added_pickings = self.return_picking_ids - self.mapped('invoice_line_ids.return_picking_id')
        deleted_pickings = self.mapped('invoice_line_ids.return_picking_id') - self.return_picking_ids
        # self.invoice_line_ids.filtered(lambda l: l.return_picking_id and l.return_picking_id in deleted_pickings).unlink()
        deleted_invoice_lines = self.invoice_line_ids.filtered(lambda l: l.return_picking_id and l.return_picking_id in deleted_pickings)
        deleted_lines = [(2,l.id,) for l in deleted_invoice_lines]
        for pick in added_pickings:
            for move in pick.move_lines:
                last_purchase_line = self.env['account.invoice.line'].search(
                    [('invoice_id.partner_id', '=', self.partner_id.id),
                     ('product_id', '=', move.product_id.id),
                     ('invoice_id.state', 'in', ['open', 'paid'])],
                    limit=1, order='create_date')
                fpos = self.fiscal_position_id
                company = self.company_id
                type = self.type
                account = self.get_invoice_line_account(type, move.product_id, fpos, company)

                new_invoice_lines.append((0,0,{
                    'product_id': move.product_id.id,
                    'return_picking_id': pick.id,
                    'quantity': move.quantity_done or 1,
                    'price_unit': last_purchase_line.price_unit,
                    'name': move.product_id.name,
                    # 'account_id': last_purchase_line.account_id.id,
                    'account_id': account.id,
                    'invoice_line_tax_ids': [(6, 0, tuple(last_purchase_line.invoice_line_tax_ids.ids))],
                    'uom_id': last_purchase_line.uom_id.id,
                    'discount': last_purchase_line.discount,
                }))

        self.update({'invoice_line_ids': deleted_lines + new_invoice_lines})

        # self.update({'invoice_line_ids': new_invoice_lines})



class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    return_picking_id = fields.Many2one(comodel_name="stock.picking")

