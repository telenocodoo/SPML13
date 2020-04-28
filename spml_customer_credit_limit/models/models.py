# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if not self.partner_id.is_credit_limit_allowed:
            return res
        account_move_obj = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),
                                                            ('state', '=', 'posted')])
        if account_move_obj:
            for account in account_move_obj:
                invoice_date = account.invoice_date
                today = fields.date.today()
                difference_in_days = (today - invoice_date).days
                if difference_in_days >= 60:
                    raise UserError(_("This customer not allowed to"
                                      " buy any thing please check "
                                      "his invoice '%s'")%(account.name))
        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_credit_limit_allowed = fields.Boolean()

    def open_partner_ledger(self):
        res = super(ResPartner, self).open_partner_ledger()
        res['name'] = 'Customer statement'
        return res
