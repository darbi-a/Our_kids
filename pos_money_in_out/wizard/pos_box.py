from odoo import models, fields, api, _
from odoo.exceptions import UserError

# class CashBox(models.TransientModel):
#     _register = False
#
#     name = fields.Char(string='Reason', required=True)
#     # Attention, we don't set a domain, because there is a journal_type key
#     # in the context of the action
#     amount = fields.Float(string='Amount', digits=0, required=True)
#
#     @api.multi
#     def run(self):
#         context = dict(self._context or {})
#         active_model = context.get('active_model', False)
#         active_ids = context.get('active_ids', [])
#
#         records = self.env[active_model].browse(active_ids)
#
#         return self._run(records)
#
#     @api.multi
#     def _run(self, records):
#         for box in self:
#             for record in records:
#                 if not record.journal_id:
#                     raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
#                 if not record.journal_id.company_id.transfer_account_id:
#                     raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
#                 box._create_bank_statement_line(record)
#         return {}
#
#     @api.one
#     def _create_bank_statement_line(self, record):
#         if record.state == 'confirm':
#             raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
#         values = self._calculate_values_for_statement_line(record)
#         return record.write({'line_ids': [(0, False, values)]})


class CashBoxIn(models.TransientModel):
    _inherit = 'cash.box.in'

    journal_id = fields.Many2one(comodel_name="account.journal",domain=[('pos_money_log', '=',True)], string="Journal", required=True, )
    money_in_type = fields.Many2one(comodel_name="box.in.type", string="Reason", required=True, )
    description = fields.Char(string="Description", required=True, )

    @api.onchange('money_in_type','description')
    def onchange_reason(self):
        if self.money_in_type and self.description:
            self.name = self.money_in_type.name + ' - '+ self.description

        pass

    @api.multi
    def _calculate_values_for_statement_line(self, record):
        if not self.journal_id.company_id.transfer_account_id:
            raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
        print("self.journal_id in==",record)
        context = dict(self._context or {})
        active_id = context.get('active_id', [])
        print("self.journal_id active_ids==", active_id)
        print("self.journal_id in context==", context)


        self.env['box.log'].create({ 'name':self.name,
                                     'journal_id':self.journal_id.id,
                                     'type':'in',
                                     'reason': self.money_in_type.name,
                                     'session_id':active_id,
                                     'amount':self.amount})
        return {
            'date': record.date,
            'statement_id': record.id,
            'journal_id': self.journal_id.id,
            'journal_box_id': self.journal_id.id,
            'amount': self.amount or 0.0,
            'account_id': self.journal_id.company_id.transfer_account_id.id,
            'ref': 'Money Box',
            'name': self.name,
        }


class CashBoxOut(models.TransientModel):
    _inherit = 'cash.box.out'

    journal_id = fields.Many2one(comodel_name="account.journal",domain=[('pos_money_log', '=',True)], string="Journal", required=True, )
    money_out_type = fields.Many2one(comodel_name="box.out.type", string="Reason", required=True, )
    description = fields.Char(string="Description", required=True, )

    @api.onchange('money_out_type', 'description')
    def onchange_reason(self):
        if self.money_out_type and self.description:
            self.name = self.money_out_type.name + ' - ' + self.description

        pass

    @api.multi
    def _calculate_values_for_statement_line(self, record):
        if not self.journal_id.company_id.transfer_account_id:
            raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
        amount = self.amount or 0.0
        context = dict(self._context or {})
        active_id = context.get('active_id', [])
        self.env['box.log'].create({'name': self.name,
                         'journal_id': self.journal_id.id,
                         'reason': self.money_out_type.name,
                         'type': 'out',
                         'session_id': active_id,
                         'amount': self.amount})

        print("self.journal_id out==", self.journal_id)
        return {
            'date': record.date,
            'statement_id': record.id,
            'journal_id': self.journal_id.id,
            'journal_box_id': self.journal_id.id,
            'amount': -amount if amount > 0.0 else amount,
            'account_id': self.journal_id.company_id.transfer_account_id.id,
            'name': self.name,
            'ref': 'Money Box',
        }



