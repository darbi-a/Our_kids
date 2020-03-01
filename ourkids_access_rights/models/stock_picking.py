# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    location_rel_id = fields.Many2one(comodel_name="stock.location", related='location_id',readonly=True )
    location_rel_dest_id = fields.Many2one(comodel_name="stock.location", related='location_dest_id',readonly=True )


