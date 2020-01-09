# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_approved = fields.Boolean()

    # @api.multi
    def action_confirm_approve(self):
        self.is_approved = True

    # @api.multi
    def action_cancel(self):
        commission_id = self.env['crm.commission.line']
        commission_id_obj = commission_id.search([('sale_id', '=', self.id)])
        if commission_id_obj:
            commission_id_obj.unlink()
        return super(SaleOrder, self).action_cancel()

    # @api.multi
    def action_draft(self):
        self.is_approved = False
        return super(SaleOrder, self).action_draft()

    # @api.multi
    def action_confirm(self):
        commission_id = self.env['crm.commission.line']
        for rec in self:
            if rec.is_approved == False:
                for line in rec.order_line:
                    if line.discount:
                        if line.discount > rec.team_id.discount_to:
                            raise UserError(_("You need to approve from sales team manager"))
            if rec.team_id.sales_commission > 0.0:
                commission_id.create({
                    'sales_team_id': rec.team_id.id,
                    'sale_id': rec.id,
                    'date': fields.datetime.today(),
                    'sales_commission': (rec.team_id.sales_commission * rec.amount_total)/100,
                })
        return super(SaleOrder, self).action_confirm()
