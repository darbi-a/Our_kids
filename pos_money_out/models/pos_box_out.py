from odoo import api,fields , _
from odoo.exceptions import UserError

from odoo.addons.account.wizard.pos_box import CashBox
from odoo.addons.point_of_sale.wizard.pos_box import PosBox


class PosBoxOut(PosBox):
    _inherit = 'cash.box.out'

    type_id = fields.Many2one(comodel_name="money.out.type", string="Type", required=False, )

    @api.onchange('type_id')
    def onchange_type(self):
        if self.type_id:
            self.name = self.type_id.name

