# -*- coding: utf-8 -*-
<<<<<<< HEAD
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
=======
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vinaya @ Cybrosys, (odoo@cybrosys.com)
#            Mohammed Shahil M P @ Cybrosys, (odoo@cybrosys.com)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
>>>>>>> b1379c668301268cf4eec9da14504d2694f756c5
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
<<<<<<< HEAD
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Customer Sequence",
    'version': '12.0.1.0.0',
    'summary': """Unique Customer Code""",
    'description': """
       Each customer have unique number code
=======
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': "Customer Sequence",
    'version': '13.0.1.0.0',
    'summary': """Unique Customer Code""",
    'description': """
       Each customer have unique number code, Odoo 13, Odoo
>>>>>>> b1379c668301268cf4eec9da14504d2694f756c5
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'views/res_partner_fom.xml',
        'views/res_company.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
<<<<<<< HEAD
    'license': 'LGPL-3',
=======
    'license': 'AGPL-3',
>>>>>>> b1379c668301268cf4eec9da14504d2694f756c5
    'installable': True,
    'application': False
}
