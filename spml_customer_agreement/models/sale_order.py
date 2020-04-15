# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_agreement_id = fields.Many2one("customer.tender.agreement")
    customer_agreement_line_id = fields.Many2one("customer.tender.agreement.line")

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

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # p = []
        if self.customer_agreement_id:
            for i in self.customer_agreement_id.product_ids:
                if i.product_id.id == self.product_id.id:
                    i.delivery_qty += self.product_uom_qty
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
            return {'domain': {'customer_agreement_id': [('id', 'in', p)]}}

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