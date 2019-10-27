# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': """Account Move Picking""",
    'summary': """ Link Account Move With Picking in Invoice and Bills and print Journal Entries""",
    'author': "Ahmed Amen",
    "version": "12.2",
    "category": "Accounting",
    "depends": [
        "stock",
        "purchase",
        "account",
    ],
    "data": [
        "views/invoice_bill_views.xml",
        "reports/report_template.xml",
    ],
    "installable": True,
}
