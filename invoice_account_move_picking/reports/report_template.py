# -*- coding: utf-8 -*-
import time
import re
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class Reportquittance_report(models.AbstractModel):

    _name = 'report.invoice_account_move_picking.consolidated_journals_view'


    def _get_report_data(self, ids):
        data = []
        entr_lst=[]
        for rec in ids:
            stock_move = self.env['stock.move'].search([('picking_id', '=', rec)])
            account_move = self.env['account.move'].search([('stock_move_id', 'in', stock_move.ids)])
            for move in account_move:
                for line in move.line_ids:
                    curt_line={'acc':line.account_id.id,'acc_name':line.account_id.display_name,'partner':line.partner_id,'debit':line.debit, 'credit':line.credit}
                    if not entr_lst:
                        entr_lst.append(curt_line)
                        continue
                    f = list(filter(lambda acc: acc['acc'] == curt_line['acc'], entr_lst))
                    if not f:
                        entr_lst.append(curt_line)
                        continue
                    else:
                        f[0]['debit'] += curt_line['debit']
                        f[0]['credit'] += curt_line['credit']
                        continue



        for r in entr_lst:

            res = {
                "acc": r['acc_name'],
                "partner": r['partner'].name,
                "debit": round(r['debit'],2),
                "credit": round(r['credit'],2),

            }
            data.append(res)
        if data:
            return data
        else:
            return {}


    @api.model
    def _get_report_values(self, docids, data=None):
        inv_ids = self.env['account.invoice'].browse(docids)
        pick_lst=[]
        for rec in inv_ids:
            picking = self.env['stock.picking'].search([('origin', '=', rec.origin)])
            pick_lst = list(set(pick_lst + picking.ids))
        moves = self.env['stock.picking'].browse(pick_lst)
        stock_move = self.env['stock.move'].search([('picking_id', '=', moves.ids[0])])
        account_move = self.env['account.move'].search([('stock_move_id', 'in', stock_move.ids)],limit=1)


        docs = self._get_report_data(pick_lst)
        debit = [x['debit'] for x in docs]
        credit = [x['credit'] for x in docs]

        return {
            'docs': docs,
            'moves': moves,
            'journal': account_move,
            'debit': sum(debit),
            'credit': sum(credit),

        }
