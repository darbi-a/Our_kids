# -*- coding: utf-8 -*-
{
    'name': "Vendor Payments Report",

    'summary': """
        Vendor Payments Report """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_journal.xml',
        'views/res_partner.xml',
        'wizard/vendor_payments.xml',
        'report/report_vendor_payments.xml',
    ],



}