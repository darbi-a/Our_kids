# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from collections import deque
from odoo.exceptions import UserError


class stock_quant(models.Model):
    _inherit = 'stock.quant'


    cost = fields.Float(string="Total Cost",  required=False, compute='_compute_cost',store=True )
    unit_cost = fields.Float(string="Unit Cost",  required=False, related='product_id.unit_cost',store=True )

    @api.one
    @api.depends('product_id', 'quantity')
    def _compute_cost(self):
        for rec in self:
            rec.cost=rec.unit_cost * rec.quantity



class stock_move(models.Model):
    _inherit = 'stock.move'


    subtotal = fields.Float(string="Subtotal",  required=False, compute='_compute_suptotal' )
    unit_cost = fields.Float(string="Unit Cost",  required=False,related='product_id.unit_cost' )

    @api.one
    @api.depends('product_id','quantity_done')
    def _compute_suptotal(self):
        for rec in self:
            rec.subtotal=rec.unit_cost * rec.quantity_done


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        super(stock_picking, self).action_done()
        for line in self.move_ids_without_package:
            if line.state == 'done':
                    line.product_id._compute_last_cost()
                    # if line.product_id.categ_id.property_cost_method == 'fifo':
                    quant=self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',self.location_dest_id.id)],limit=1 )
                    quant.sudo().write({'unit_cost': line.product_id.unit_cost})
                    quant.sudo().write({'cost': line.product_id.unit_cost * quant.quantity })




