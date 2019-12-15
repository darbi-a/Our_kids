# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime , date ,timedelta

import calendar

import logging

LOGGER = logging.getLogger(__name__)

class PosPromotion(models.Model):
    _name = 'pos.promotion'
    _rec_name = 'name'
    _description = 'Point Of Sale Promotions'
    #_order = 'name asc, id desc'

    def _get_date_from_now(self):
        today = datetime.now().today()
        first_day_this_month = date(day=1, month=today.month, year=today.year)
        return first_day_this_month

    def _get_date_to(self):
        # import calendar
        today = datetime.now().today()
        last_day = calendar.monthrange(today.year,today.month)[1]
        last_day_this_month = date(day=last_day, month=today.month, year=today.year)
        return last_day_this_month

    name = fields.Char(string="Name", required=False, )
    code = fields.Char(string="Code", required=False, )
    ordered_product_id = fields.Many2one(comodel_name="product.product")
    gift_product_id = fields.Many2one(comodel_name="product.product")
    ordered_quantity = fields.Integer()
    gift_quantity = fields.Integer()

    date_from = fields.Date(string="Date From",default=_get_date_from_now , required=False, )
    date_to = fields.Date(string="Date To",default=_get_date_to , required=False, )

    automatically_applied = fields.Boolean()

    applied_on_customers = fields.Selection(default="all", selection=[('all', 'All'), ('specific', 'Specific'), ], required=False, )
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Customers", )

    applied_on_pos = fields.Selection(default="all", selection=[('all', 'All'), ('specific', 'Specific'), ], required=False, )
    pos_ids = fields.Many2many(comodel_name="pos.config",string="Point Of Sales" )

    active = fields.Boolean(string="Active", default=True)

    pos_orders_ids = fields.Many2many(comodel_name="pos.order", relation="pos_order_promotion_rel", column1="promo_id", column2="order_id")
    
    order_count = fields.Integer(compute='compute_order_count')

    pos_config_ids = fields.Many2many(comodel_name="pos.config", relation="pos_config_promotion_rel", column1="config_id", column2="promotion_id", string="Applied In Pos", )
    
    @api.model
    def create(self,vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('pos.promotion')
        return super(PosPromotion,self).create(vals)

    @api.multi
    def toggle_active(self):
        for rec in self:
            rec.active = not rec.active
            
    def compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.pos_orders_ids)
            
    def action_show_orders(self):
        for one in self:
            domain = [('id', 'in', self.pos_orders_ids.ids)]
            view_tree = {
                'name': _(' Pos Orders '),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'pos.order',
                'type': 'ir.actions.act_window',
                'domain': domain,

            }

            return view_tree
            

