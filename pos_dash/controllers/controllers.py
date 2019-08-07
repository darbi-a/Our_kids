# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import Controller, request, route
import base64

from datetime import date
from datetime import datetime
import datetime as DT
import unicodedata
d = date.today()

class Dashboard(http.Controller):
    @http.route(['/dashboard?<q_time>','/dashboard/<s_type>','/dashboard'], auth='user', website=True)
    def index(self, s_type="",q_time="",**kw):
        if request.env.user.has_group('point_of_sale.group_pos_manager'):
            try:
                cr = request.cr
                q= str(kw.get("q"))

                day = datetime.combine(d, datetime.min.time())



                if s_type is None and q is None:
                    s_type= "day"
                act = "d"
                if s_type == "day":
                    act = "d"
                    day = datetime.combine(d, datetime.min.time())
                if s_type =="week":
                    act = "w"
                    day= day - DT.timedelta(days=7)
                if s_type =="month":
                    act = "m"
                    day= day - DT.timedelta(days=30)
                if s_type =="3months":
                    act = "3m"
                    day= day - DT.timedelta(days=90)
                if s_type =="6months":
                    act = "6m"
                    day= day - DT.timedelta(days=180)
                if s_type == "year":
                    act = "y"
                    day = day - DT.timedelta(days=365)

                # if "?q=" in
                end_date =  datetime.combine(d, datetime.max.time())
                end_date = str(end_date).split('.')[0]

                start_date = str(day).split('.')[0]
                if q !="None":
                    q_list = q.split('?')
                    start_date = q_list[0]
                    end_date = q_list[1]
                    print ("end date : ",end_date)
                    if end_date =="":
                        end_date = datetime.combine(d, datetime.max.time())
                        end_date = str(end_date).split('.')[0]
                    if start_date == "":
                        start_date = day - DT.timedelta(days= 5*365)
                        start_date = str(start_date).split('.')[0]
                        print ("start_date : ",start_date)
                    act = "check"

                query = """SELECT
                    s.user_id , SUM(l.price_subtotal_incl)  AS price 
                    FROM pos_order_line AS l
                    LEFT JOIN pos_order s ON (s.id=l.order_id)
                    where date_order between '%s' and '%s' 
                    GROUP BY s.user_id
                    ORDER BY price DESC 
                         """%(start_date,end_date)

                users_names = []
                amount=[]
                orders_num = []

                cr.execute(query)
                result=cr.dictfetchall()

                for r in result:
                    price = int(r['price'])
                    amount.append( price)
                    user_id = int(r['user_id'])
                    name = request.env['res.users'].search([('id', '=', user_id)]).name
                    users_names.append(str(name))

                total_amount=sum(amount)
                orders = request.env['pos.order'].search(['&',('date_order','>=',start_date),('date_order','<=',end_date)])
                orders_n = len(orders)
                if total_amount == 0:
                    average=0
                else:
                    average = round(total_amount / orders_n,1)

                query = """SELECT
                     l.product_id,SUM(l.price_subtotal_incl)  AS price 
                    FROM pos_order_line AS l
                    LEFT JOIN pos_order s ON (s.id=l.order_id)
                    LEFT JOIN product_product p ON (l.product_id=p.id)
                    where date_order between '%s' and '%s'  
                    GROUP BY l.product_id
                    ORDER BY price DESC 
                    LIMIT 7 """%(start_date,end_date)

                cr.execute(query)
                result = cr.dictfetchall()
                prods_name = []
                prods_num = []

                for r in result:
                    pr_id = int(r['product_id'])
                    pr_name = request.env['product.product'].search([('id', '=', pr_id)]).name.encode("utf-8")
                    pr_price = int(r['price'])
                    prods_name.append(pr_name)
                    prods_num.append(pr_price)


                query=""" SELECT
                     pt.pos_categ_id,SUM(l.price_subtotal_incl)  AS price 
                    FROM pos_order_line AS l
                    LEFT JOIN pos_order s ON (s.id=l.order_id)
                    LEFT JOIN product_product p ON (l.product_id=p.id)
                    LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                    LEFT JOIN pos_category c ON (pt.pos_categ_id=c.id)            
                    where date_order between '%s' and '%s'  
                    GROUP BY pt.pos_categ_id
                    ORDER BY price DESC 
                    LIMIT 7 """%(start_date,end_date)

                cr.execute(query)
                result = cr.dictfetchall()

                cat_names = []
                cat_num = []
                for r in result:
                    categ = r['pos_categ_id']
                    if categ is None:
                        categ_name = "None"
                    else:
                        categ_id = int(categ)
                        categ_name = request.env['pos.category'].search([('id', '=', categ_id)]).name

                    categ_amount = int(r['price'])
                    categ_name = str(categ_name)
                    cat_names.append(categ_name)
                    cat_num.append(categ_amount)

                hours =list( range(0, 24))
                num_hours = [0] * 24
                print(hours)

                query = """SELECT
                    extract(hour from date_order) AS hour ,count(s.id)            
                    FROM pos_order_line AS l
                    LEFT JOIN pos_order s ON (s.id=l.order_id)
                    
                    where date_order between '%s' and '%s' 
                    GROUP BY hour
                    order by count desc
                    """%(start_date,end_date)
                cr.execute(query)
                result = cr.dictfetchall()
                rush_hour=0

                if len(result):
                    # New change add 2 hours for timezone adjustment
                    rush_hour=int(result[0]['hour']) + 2
                rush_hour2 = rush_hour +1

                if rush_hour> 12 :
                    rush_hour%=12
                    rush_hour=str(rush_hour)+ " pm"
                else:
                    rush_hour=str(rush_hour)+" am"


                if rush_hour2 > 12 :
                    rush_hour2 %=12
                    rush_hour2 =str(rush_hour2 )+ " pm"
                else:
                    rush_hour2 =str(rush_hour2)+" am"
                rush_hour = rush_hour + " - " + rush_hour2

                for r in result:
                    hour = int(r['hour'])
                    num = int(r['count'])
                    num_hours[hour]=num

                if ' ' in start_date:
                    start_date = start_date.split(' ')[0]
                    end_date = end_date.split(' ')[0]
            except Exception as ex:
                print ("Error !!!!!!!")
                print (str(ex))
                return request.redirect("/")

            return http.request.render('pos_dash.dashboard', {
            'orders_n':orders_n,
            'total_amount':total_amount,
            'average':average,
            "users_names": users_names,
            'orders_num':orders_num,"amount":amount,
            "cat_names":cat_names,
            "cat_num":cat_num,
            "act":str(act),
            "prods_name":prods_name,
            "prods_num":prods_num,
            "hours":hours,
            "num_hours":num_hours,
            "rush_hour":rush_hour,
            'start':start_date,
            'end':end_date,
        })
        else:
            return request.render('website.404')
