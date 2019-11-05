# -*- coding: utf-8 -*-

from odoo.http import request
from odoo.addons.bus.controllers.main import BusController



# class BusControllerInherit(BusController):
#     def _poll(self, dbname, channels, last, options):
#         if request.session.uid:
#             channels = list(channels)
#             channels.append((request.db, 'change_detector'))
#         return super(BusControllerInherit, self)._poll(dbname, channels, last, options)
