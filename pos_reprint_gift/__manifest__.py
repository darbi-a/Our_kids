{
    "name": "Pos extend Receipt",
    "summary": "pos_es_receipt",
    "version": "12.0.1.0",
    "category": "Point Of Sale",
    "website": "https://www.itss-c.com",
    "author": "Khalil Al Sharif",
    "license": "",
    "application": False,
    "installable": True,
    "depends": [
        "point_of_sale",
    ],
    "qweb": [
        'static/src/xml/receipt.xml'
    ],
    "data": [
        'views/templates.xml',
    ],

}
