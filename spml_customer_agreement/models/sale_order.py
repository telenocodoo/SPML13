# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_agreement_id = fields.Many2one("customer.tender.agreement")
    customer_agreement_line_id = fields.Many2one("customer.tender.agreement.line")

    @api.depends('customer_agreement_id')
    @api.onchange('product_id')
    def _onchange_customer_agreement_id(self):
        p = []
        if self.customer_agreement_id:
            for i in self.customer_agreement_id.product_ids:
                if i.remain_qty > 0:
                    p.append(i.product_id.id)
                # print("44444444444",i.product_id.name)
                # print({'domain': {'product_id':[('product_id','in',p)]}})
            return {'domain': {'product_id':[('id', 'in', p)]}}

    @api.depends('customer_agreement_id')
    @api.onchange('product_id')
    def _onchange_customer_agreement_id2(self):
        for record in self:
            if record.customer_agreement_id:
                for i in record.customer_agreement_id.product_ids:
                    if i.product_id.id ==  record.product_id.id:
                        record.product_uom_qty = i.remain_qty
                #         p.append(i.product_id.id)
                #     # print("44444444444",i.product_id.name)
                #     # print({'domain': {'product_id':[('product_id','in',p)]}})
                # return {'domain': {'product_id':[('id', 'in', p)]}}

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # p = []
        for record in self:
            if record.customer_agreement_id:
                for i in record.customer_agreement_id.product_ids:
                    if i.product_id.id == record.product_id.id:
                        if record.product_uom_qty > i.remain_qty:
                            raise UserError(_("This Qty Is Not Available"))
                # p.append(i.product_id.id)
                # print("44444444444",i.product_id.name)
                # print({'domain': {'product_id':[('product_id','in',p)]}})
            # return {'domain': {'product_id':[('id', 'in', p)]}}

class SaleOrder(models.Model):
    _inherit = "sale.order"

    customer_agreement_id = fields.Many2one("customer.tender.agreement")
    # to_id = fields.Many2one("res.partner")
    # departure_time = fields.Datetime()
    # arrival_time = fields.Datetime()
    # transportation_ids = fields.One2many('transportation.operation', 'sale_id', string='Transfers')

    @api.onchange('partner_id')
    def _onchange_customer_agreement_id(self):
        p = []
        for record in self:
            agreement_ids = self.env['customer.tender.agreement'].search([('partner_id', '=', record.partner_id.id)])
            if agreement_ids:
                for i in agreement_ids:
                    p.append(i.id)
            return {'domain': {'customer_agreement_id': [('id', 'in', p)]},}

    # @api.onchange('partner_id')
    # def _onchange_partner_id2(self):
    #     # p = []
    #     # for record in self:
    #     #     agreement_ids = self.env['customer.tender.agreement'].search([('partner_id', '=', record.partner_id.id)])
    #     #     if agreement_ids:
    #     #         for i in agreement_ids:
    #     #             p.append(i.id)
    #     return {'domain': {'partner_id': [('search_default_customer','=', 1),
    #                                 ('res_partner_search_mode','=', 'customer'),
    #                                 ('default_customer_rank','=',1)
    #                                 ]
    #                 }}

    def action_confirm(self):
        for record in self:
            if record.customer_agreement_id:
                for line in record.order_line:
                    for agreement in record.customer_agreement_id.product_ids:
                        if line.product_id.id == agreement.product_id.id:
                            if line.product_uom_qty > agreement.remain_qty:
                                raise UserError(_("You Aren't Allowed To Order This Qty"))
                            agreement.delivery_qty += line.product_uom_qty
        res = super(SaleOrder, self).action_confirm()
        return res

    # @api.onchange('customer_agreement_id')
    # def _onchange_customer_agreement_id(self):
    #     if self.customer_agreement_id:
    #         print("111111111111")
    #         # if self.order_line:
    #         #     self.order_line = False
    #         for record in self.customer_agreement_id.product_ids:
    #             print("111111111111222222222222")
    #             res = {
    #                 'order_id': self._origin.id,
    #                 'product_id': record.product_id.id,
    #                 # 'category_id': record.category_id.id,
    #                 # 'is_conditional': record.is_conditional,
    #             }
    #             print("33333333333", res)
    #             # self.write({
    #             #     'order_line': [(0, 0, res)],
    #             # })
    #             self.order_line.new(res)