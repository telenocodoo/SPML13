# -*- coding: utf-8 -*-
{
    'name': "SPML UOM",
    'summary': """SPML UOM""",
    'description': """SPML UOM""",
    'author': "Magdy,TeleNoc",
    'website': "https://telenoc.org",
    'category': 'manufacture',
    'version': '0.13',
    'depends': ['mrp', 'spml_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'report/production_order_report.xml',
        'views/mrp_bom.xml',
        'views/scrap_reason.xml',
    ],
}
