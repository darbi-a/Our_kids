# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
class account_invoice(models.Model):
    _inherit = 'account.invoice'

    tax_lines = fields.Many2many(comodel_name="account.tax", string="Line Tax",readonly=True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )

    @api.onchange("tax_lines")
    def onchange_line_tax_lines(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                print("line ",line)
                line.invoice_line_tax_ids =[(6, 0, self.tax_lines.ids)]
                # line.sudo().write({'tax_id':[(6, 0, self.tax_lines.ids)]})
                print("line tax_id ", line.invoice_line_tax_ids)

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'



    @api.onchange('product_id')
    def onchange_product_id(self):
        # super(account_invoice_line, self).onchange_product_id()
        print("self.order_id",self.invoice_id)
        print("self.order_id bb",self.invoice_id.tax_lines.ids)
        if self.invoice_id.tax_lines:
            ids = self.invoice_id.tax_lines.ids
            self.invoice_line_tax_ids = [(6, 0, ids)]
            # self.sudo().write({'tax_id' : [(6, 0, ids)]})
            print("line tax_id ", self.invoice_line_tax_ids)
