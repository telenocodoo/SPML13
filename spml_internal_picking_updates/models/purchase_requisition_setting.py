from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_source_id = fields.Many2one('stock.location')
    picking_type_id = fields.Many2one('stock.picking.type')


class RequisitionConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    purchase_source_id = fields.Many2one('stock.location', string='Source Location',
                                         default=lambda self: self.env.user.company_id.purchase_source_id)
    picking_type_id = fields.Many2one('stock.picking.type',
                                      default=lambda self: self.env.user.company_id.picking_type_id)

    @api.model
    def create(self, values):
        if 'company_id' in values \
                or 'purchase_source_id' in values or 'picking_type_id' in values:
            self.env.user.company_id.write({
                    'purchase_source_id': values['purchase_source_id'],
                    'picking_type_id': values['picking_type_id'],
                 })
        res = super(RequisitionConfigSettings, self).create(values)
        return res
