# -*- coding: utf-8 -*-
{
    'name': "Vendor Balance Report",

    'summary': """
        Vendor Balance Report """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['account','stock','vendor_payments_report','product_season'],

    # always loaded
    'data': [
        # 'views/res_partner.xml',
        'views/account_payment.xml',
        'wizard/vendor_balance_report_wizard.xml',
        'report/report_vendor_balance.xml',
        'views/account_move.xml',
        'views/account_journal.xml',
    ],



}