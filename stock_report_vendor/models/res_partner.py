# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tag_id = fields.Many2one(comodel_name="res.partner.category", string="Tag")

    @api.model
    def create(self,vals):
        if vals.get('tag_id'):
            vals['category_id'] = [(6,0,[vals.get('tag_id')])]
        return super(ResPartner,self).create(vals)

    @api.multi
    def write(self,vals):
        if vals.get('tag_id'):
            vals['category_id'] = [(6,0,[vals.get('tag_id')])]
        return super(ResPartner,self).write(vals)

