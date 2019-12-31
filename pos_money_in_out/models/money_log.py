# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque

class box_log(models.Model):
    _name = 'box.log'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="Description", required=True,)
    reason = fields.Char(string="Reason",)
    type = fields.Selection(string="Type", selection=[('in', 'Money In'), ('out', 'Money Out'), ], required=False, )
    date = fields.Date(string="Date", required=False,default=fields.Date.today() )
    amount = fields.Float(string="Amount",  required=False, )

    journal_id = fields.Many2one(comodel_name="account.journal", domain=[('pos_money_log', '=', True)],
                                 string="Journal", required=True, )
    session_id = fields.Many2one(comodel_name="pos.session", string="Session", required=False, )
    config_id = fields.Many2one(comodel_name="pos.config", string="Point Of Sale", required=False, )

class box_in_type(models.Model):
    _name = 'box.in.type'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()


class box_out_type(models.Model):
    _name = 'box.out.type'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    journal_id = fields.Many2one('account.journal',  string='Journal',compute="compute_journal", store=True,
                                 readonly=True)
    journal_box_id = fields.Many2one('account.journal', string='Journal', store=True,
                                     readonly=True)


    @api.one
    @api.depends('journal_box_id','statement_id')
    def compute_journal(self):
        for stat in self:
            if stat.journal_box_id:
                stat.journal_id=stat.journal_box_id.id
            else:
                stat.journal_id = stat.statement_id.journal_id.id
