# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    reason_id = fields.Many2one('scrap.reason')

    @api.onchange('reason_id')
    def onchange_reason_id(self):
        if self.reason_id:
            self.scrap_location_id = self.reason_id.scrap_location_id


class ScrapReason(models.Model):
    _name = 'scrap.reason'

    name = fields.Char(string="Name")
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location',
                                        domain="[('scrap_location', '=', True)]", required=True,
                                     )

