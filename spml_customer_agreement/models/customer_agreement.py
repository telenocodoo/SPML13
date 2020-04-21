# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class CustomerTenderAgreement(models.Model):
    _name = 'customer.tender.agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    partner_id = fields.Many2one('res.partner')
    product_ids = fields.One2many('customer.tender.agreement.line', 'agreement_id')


class CustomerTenderAgreementLine(models.Model):
    _name = 'customer.tender.agreement.line'

    agreement_id = fields.Many2one('customer.tender.agreement')
    product_id = fields.Many2one('product.product')
    description = fields.Char()
    quantity = fields.Float()
    uom_id = fields.Many2one('uom.uom')
    delivery_qty = fields.Float()
    unit_price = fields.Float()
    remain_qty = fields.Float(compute="get_remain_qty", store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.uom_id = self.product_id.uom_id.id
            self.unit_price = self.product_id.lst_price

    @api.depends('quantity','delivery_qty')
    def get_remain_qty(self):
        for record in self:
            if record.delivery_qty or record.quantity:
                record.remain_qty = record.quantity - record.delivery_qty

