from odoo import models, fields, api

class BankAccount(models.Model):
    _inherit = 'account.bank.statement.line'

    bank_account = fields.Many2one('account.account', 'Account')
    employee_name = fields.Many2one('hr.employee', 'Employee')


class BankAccount(models.Model):
    _inherit = 'stock.picking'

