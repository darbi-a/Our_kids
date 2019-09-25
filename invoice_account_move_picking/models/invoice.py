# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _


class account_invouce(models.Model):
    _inherit = 'account.invoice'

    journal_entries_count = fields.Integer(compute='compute_journal_entries_count', store=True)

    def compute_journal_entries_count(self):
        for rec in self:
            picking = self.env['stock.picking'].search([('origin', '=', rec.origin)])
            stock_move = self.env['stock.move'].search([('picking_id', '=', picking.ids)])
            account_move = self.env['account.move'].search([('stock_move_id', 'in', stock_move.ids)])
            rec.journal_entries_count = len(account_move)

    @api.multi
    def action_open_order(self):
        for rec in self:
            picking = self.env['stock.picking'].search([('origin', '=', rec.origin)])
            stock_move = self.env['stock.move'].search([('picking_id', '=', picking.ids)])
            account_move = self.env['account.move'].search([('stock_move_id', 'in', stock_move.ids)])
            rec.journal_entries_count = len(account_move)

            domain = [('id', 'in', account_move.ids)]
            view_tree = {
                'name': _(' Journal Entries '),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'domain': domain,
                'readonly': True,
            }

            return view_tree




