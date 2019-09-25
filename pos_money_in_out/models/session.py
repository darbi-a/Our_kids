# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from collections import deque

class pos_session(models.Model):
    _inherit = 'pos.session'




    log_count = fields.Integer(compute='compute_money_log_count',)

    def compute_money_log_count(self):
        for rec in self:

            logs = self.env['box.log'].search([('session_id', '=', rec.id)])
            rec.log_count = len(logs)

    @api.multi
    def open_money_log(self):
        for rec in self:
            logs = self.env['box.log'].search([('session_id', '=', rec.id)])

            domain = [('id', 'in', logs.ids)]
            view_tree = {
                'name': _(' Money Box IN/OUT '),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'box.log',
                'type': 'ir.actions.act_window',
                'domain': domain,
                'readonly': True,
            }

            return view_tree


