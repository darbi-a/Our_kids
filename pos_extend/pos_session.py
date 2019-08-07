# -*- coding: utf-8 -*-
from odoo import api, fields, models , _

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal', store=True)
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal', store=True)

class PosConfig(models.Model):
    _inherit = "pos.config"

    def session_payment(self):

        for res in self:
            details = []
            bg_colore = [ '', 'cadetblue', 'rosybrown', 'rosyblue', 'coral', 'darkcyan', 'lightcoral', 'cornflowerblue', 'cadetblue', 'rosybrown', 'rosyblue', 'coral', 'darkcyan', 'lightcoral', 'cornflowerblue' ]
            total = 0
            for session in res.session_ids:
                payment_id = self.env['account.bank.statement'].search([('name', '=', session.name)])
                for each in payment_id:
                    session_id = self.env['pos.session'].search([('name', '=', each.name)])
                    if session_id.state == 'opened':
                        #print "%%%%%%%%%%%%%%%%%%%%%%%",each.currency_id.name
                        #print "Journal namee get",each.journal_id.name_get()[0][1]
                        details.append({'payment':each.journal_id.name_get()[0][1],
                                        'amount':each.total_entry_encoding,
                                        'currency':each.currency_id.symbol})
                        total += each.total_entry_encoding
                #print "\n details-000000000----", details
            body = """<table  style='width: 100%;'>"""
            count = 0
            for data in details:
               #print "#######################",data['currency']
               count += 1
               size = (data['amount'] * 100) / total  if data['amount'] else 0
               body += """<tr>"""
               body += """<td style="text-align:left;width: 40%;/* font-size: 16px; */color: blue;">""" + data['payment'] + """</td>"""
               body += """<td style="text-align:left; width: 70%;">
               <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
                    style="width:""" + '100' + """%;background-color:white;border-radius:10px;height:16px; -moz-border-radius: 3px;-webkit-border-radius:
                                10px;border:1px solid #f0eeef;">
                    <div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
                    style="width:""" + format(size, '.0f') + """%;background-color:""" + bg_colore[count] + """;height:14px;border-radius:10px; -moz-border-radius: 3px;-webkit-border-radius:
                                10px;line-height: 14px;font-size: 10px;color:black;">""" + format(size, '.0f') + '%' + """
                                </div>
                </div>
                </td>
               """
               body += """<td style="text-align:left;color:  firebrick;width: 20%;"><div style='margin-left: 5px;'>""" + data['currency'] + str(data['amount']) + """</div></td>"""
               body += """</tr>"""
            body += "</table>"
            res.payment_details = body


    def session_total_count(self):
        session_list = self.env['pos.session'].search([('state','=','opened')])
       
        for sessions in session_list:
           # config_ids = self.env['pos.config'].search[('id','in',sessions.config_id)]
           
            for each1 in sessions.config_id:
                    each1.total_sesstion = len(sessions)
                     
                    each1.total_details_count = """
                    
                                <table style="height: 24px;" width="100%">
                                <tbody>
                                
                                    <tr>
                                        <td style="width: 55%;margin-top: 10px;">Subtotal:</td>
                                        <td style="width: 40%;margin-top: 10px;">
                                            <div class="progress mb0" style="height: 15px;width:100%" >
                                                    <div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
                                                        style="width: """ + format((each1.subtotal_session * 100) / each1.subtotal_session  if each1.subtotal_session else 0, '.0f') + """%;">
                                                         <span style="font-size:0px;display:  initial;"> """ + str(each1.subtotal_session) + """</span> 
                                                    </div>
                                            </div>
                                        </td>
                                         <td style="width: 5%;margin-bottom: 3px;">""" + str(round(each1.subtotal_session,2)) + """</td>
                                    </tr>
                                </tbody>
                            </table>
                  
                        """
                   
    def seetion_total(self):

        for rec in self:

            current_session = self.env['pos.session'].search([('id', 'in', rec.session_ids.ids)],
                                                             order='start_at desc', limit=1)
            order_id = None
            if current_session and len(current_session) == 1 and current_session.state != 'closed':
                order_id = self.env['pos.order'].search([('session_id', '=', current_session.id)])

            if order_id:
                #print "order is.......................................",order_id
                # rec.number_of_order = len(order_id)
                cancel = 0
                done = 0
                number_of_coupons = 0
                returned_amount = 0
                total_discount = 0
                for order in order_id:
                    for each in order.lines:
                        if each.product_id.type == "product":
                            rec.subtotal_session += each.price_unit * each.qty
                            rec.sale_qty += each.qty
                            # rec.untaxamount_total += each.price_unit * each.qty
                        # elif each.product_id.is_discount or each.product_id.is_coupon:
                        #     total_discount += each.price_unit * each.qty
                        #     if each.product_id.is_coupon and order.amount_total >= 0.0:
                        #         number_of_coupons += 1
                        # elif each.product_id.is_delivery:
                        #     rec.total_delivery += each.price_unit * each.qty

                        if each.discount:
                            total_discount += (each.price_unit * each.qty) - each.price_subtotal

                        # rec.sale_qty += each.qty
                    rec.untaxamount_total += order.amount_total
                    rec.tax_amount += order.amount_tax
                    if order.state == 'cancel':
                        cancel += 1
                    if order.amount_total >= 0.0 :
                        done += 1
                    if order.amount_total < 0:
                        returned_amount += order.amount_total
                rec.total_cancel_order = cancel
                rec.total_done_order = done
                rec.number_of_order = done
                rec.number_of_coupons = number_of_coupons
                rec.returned_amount = abs(returned_amount)
                rec.total_discount = abs(total_discount)

            else:
                rec.number_of_order = 0
                rec.total_discount = 0.0
                rec.total_delivery = 0.0
                rec.sale_qty = 0
                rec.total_done_order = 0
                rec.total_cancel_order = 0
                rec.subtotal_session = 0
                rec.untaxamount_total = 0
                rec.tax_amount = 0
                rec.number_of_coupons = 0
                rec.returned_amount = 0


                 
    untaxamount_total = fields.Float('Total', digits=(16,2),compute='seetion_total')
    tax_amount = fields.Float('Total VAT',digits=(16,2),compute='seetion_total')
    subtotal_session = fields.Float('Subtotal', digits=(16,2),compute='seetion_total')
    number_of_order = fields.Integer('Total Order',compute='seetion_total' )
    total_discount = fields.Float('Total discount(%)',compute='seetion_total' )
    total_delivery = fields.Float('Total discount(%)',compute='seetion_total' )
    returned_amount = fields.Float(compute='seetion_total' )
    sale_qty = fields.Integer('Total Qty Sale',compute='seetion_total' )
    number_of_coupons = fields.Integer(compute='seetion_total')
    total_done_order = fields.Integer('Total Done Order',compute='seetion_total' )
    total_cancel_order = fields.Integer('Total Cancel Order',compute='seetion_total')

    payment_details_ids = fields.One2many('account.bank.statement', string='Payments', compute='compute_payment_details_ids', readonly=True)
    payment_details = fields.Html('Payment Details', compute='session_payment')
    payment_graph = fields.Html('Payment Graph', compute='session_payment')
   
    total_details_count = fields.Html('Total Details', compute='session_total_count')
    total_sesstion = fields.Integer('Total', compute='session_total_count')

    @api.multi
    def compute_payment_details_ids(self):
        for rec in self:
            rec.payment_details_ids = rec.session_ids.mapped('statement_ids').ids
    
    @api.multi
    def get_action_pos_order(self):
        return {
                'name': _('Pos order'),
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'view_mode': 'tree',
                'view_type': 'form',
                'domain': [('session_id', '=', self.session_ids.id)],
            }

    def open_current_session(self):
        current_session = self.env['pos.session'].search([('id', 'in', self.session_ids.ids)],order='start_at desc',limit=1)
        return {
                'name': _('Pos Session'),
                'type': 'ir.actions.act_window',
                'res_model': 'pos.session',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': current_session.id,
            }


