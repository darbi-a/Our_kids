import datetime
from odoo import api, fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

TIMEOUT = 50


class Bus(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def gc(self):
        timeout_ago = datetime.datetime.utcnow()-datetime.timedelta(seconds=TIMEOUT*2)
        domain = [('create_date', '<', timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
        buses = self.sudo().search(domain,limit=1000000)
        while buses:
            buses.unlink()
            buses = self.sudo().search(domain, limit=1000000)
        return self.sudo().search(domain).unlink()


