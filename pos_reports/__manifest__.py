# -*- coding: utf-8 -*-
{
    'name': "pos Sales Reports",

    'summary': """
        pos Sales Reports """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'point of sale',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','pos_branches'],

    # always loaded
    'data': [
        'report/report_pos_by_categ.xml',
        'report/report_pos_totals.xml',
        'report/report_pos_loss_gain.xml',
        'report/report_pos_cashier_return.xml',
        'report/report_pos_cashier_sales.xml',
        'wizard/totals_report_wizard.xml',
        'wizard/pos_los_gain.xml',
        'wizard/pos_cashier_return.xml',
        'wizard/pos_cashier_sales.xml',
        'wizard/totals_pos_categ_wizard.xml',
    ],



}