# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math


class statement(models.Model):
    _inherit = 'account.bank.statement'

    @api.multi
    def button_confirm_bank(self):
        self._balance_check()
        statements = self.filtered(lambda r: r.state == 'open')
        for statement in statements:
            moves = self.env['account.move']
            # `line.journal_entry_ids` gets invalidated from the cache during the loop
            # because new move lines are being created at each iteration.
            # The below dict is to prevent the ORM to permanently refetch `line.journal_entry_ids`
            line_journal_entries = {line: line.journal_entry_ids for line in statement.line_ids}
            print("line_journal_entries == ", line_journal_entries)
            box_journal={}
            for st_line in statement.line_ids:
                print(" *** NNNNNN **")
                print("st_line == ", st_line)
                print("st_line == ", st_line.journal_id.name)
                print("st_line == ", st_line.journal_box_id.name)
                if st_line.journal_box_id:
                    box_journal.update({st_line.name : st_line.journal_box_id.id})
                    st_line.journal_id = st_line.journal_box_id.id
                # upon bank statement confirmation, look if some lines have the account_id set. It would trigger a journal entry
                # creation towards that account, with the wanted side-effect to skip that line in the bank reconciliation widget.
                journal_entries = line_journal_entries[st_line]
                print("st_line22 == ", st_line.journal_id.name)

                st_line.fast_counterpart_creation()
                print("vvv == ",st_line.fast_counterpart_creation())
                print("journal_entries == ", journal_entries)
                if not st_line.account_id and not journal_entries.ids and not st_line.statement_id.currency_id.is_zero(
                        st_line.amount):
                    raise UserError(
                        _('All the account entries lines must be processed in order to close the statement.'))
            moves = statement.mapped('line_ids.journal_entry_ids.move_id')
            print("moves == ", moves)
            for mov in moves:
                if mov.ref:
                    if 'Money Box' in mov.ref and box_journal and mov.line_ids:
                        lab=mov.line_ids[0].name
                        print('nnn =',box_journal)
                        print('nnn =',box_journal[lab])
                        mov.journal_id = box_journal[lab]
            if moves:
                moves.filtered(lambda m: m.state != 'posted').post()
            statement.message_post(body=_('Statement %s confirmed, journal items were created.') % (statement.name,))
        statements.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})
