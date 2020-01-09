# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class CrmTeam(models.Model):
    _inherit = "crm.team"

    discount_from = fields.Float(string="From")
    discount_to = fields.Float(string="To")
    sales_commission = fields.Float(string="Commission")
    commission_ids = fields.One2many('crm.commission.line', 'sales_team_id')


class CrmCommissionLine(models.Model):
    _name = "crm.commission.line"

    sales_team_id = fields.Many2one('crm.team')
    sale_id = fields.Many2one('sale.order')
    date = fields.Datetime()
    sales_commission = fields.Float(string="Commission")

