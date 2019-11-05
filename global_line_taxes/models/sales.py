# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import yaml
class sale_order(models.Model):
    _inherit = 'sale.order'

    tax_lines = fields.Many2many(comodel_name="account.tax", string="Line Tax",domain=[('type_tax_use', '=', 'sale')],readonly=True,states={'draft': [('readonly', False)]} )

    @api.multi
    def action_view_invoice(self):
        action = super(sale_order, self).action_view_invoice()
        print("action == ",action['context'])
        print("action == ",type(action['context']))
        context=yaml.load(action['context'])
        print("context == ",context)
        print("context == ",type(context))
        print("self.tax_lines == ",self.tax_lines.ids)
        context.update({'tax_lines':[(6, 0, self.tax_lines.ids)]})
        action['context']=context
        print("action == ", action['context'])
        # action['context']['default_tax_lines'] = self.tax_lines.ids
            # [(6, 0, self.tax_lines.ids)]

        return action



    @api.onchange("tax_lines")
    def onchange_line_tax_lines(self):
        for rec in self:
            for line in rec.order_line:
                print("line ",line)
                line.tax_id =[(6, 0, self.tax_lines.ids)]
                # line.sudo().write({'tax_id':[(6, 0, self.tax_lines.ids)]})
                print("line tax_id ", line.tax_id)

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'



    @api.onchange('product_id')
    def product_id_change(self):
        super(sale_order_line, self).product_id_change()

        print("self.order_id",self.order_id)
        print("self.order_id bb",self.order_id.tax_lines.ids)
        if self.order_id.tax_lines:
            ids = self.order_id.tax_lines.ids
            self.tax_id = [(6, 0, ids)]
            # self.sudo().write({'tax_id' : [(6, 0, ids)]})
            print("line tax_id ", self.tax_id)
