# -*- coding: utf-8 -*-

from openerp import api
from openerp import fields
from openerp import models
from openerp import exceptions


class inventory(models.Model):
    _inherit = 'stock.inventory'
    partner_id = fields.Many2one(
        'res.partner', 'Inventoried Owner',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('supplier', '=', True)]",
        help="Specify Owner to focus your inventory on a particular Owner.")

class picking(models.Model):
    _inherit = 'stock.picking'

    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        required=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Default Owner")