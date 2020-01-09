# -*- coding: utf-8 -*-
{
    'name': "sales team discount",
    'summary': """
        sales team discount""",
    'description': """
        sales team discount
    """,
    'author': "Magdy, helcon",
    'website': "http://www.yourcompany.com",
    'category': 'sales',
    'version': '0.1',
    'depends': ['sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sales_order.xml',
        'views/sales_team.xml',
    ],
}
