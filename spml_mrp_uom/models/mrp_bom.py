# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    stock_production_lot_id = fields.Many2one('stock.production.lot',
                                              string='Lot/Serial')
    expiration_date = fields.Date(string='Expiration Date')

    @api.onchange('stock_production_lot_id')
    def onchange_stock_production_lot_id(self):
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        lot_id = self.env['stock.production.lot'].search([('product_id.id', '=', self.product_id.id)])
        print(lot_id)
        lot_ids = []
        for l in lot_id:
            lot_ids.append(l.id)
        domain = {'stock_production_lot_id': [('id', 'in', lot_ids)]}
        self.expiration_date = self.stock_production_lot_id.life_date
        return {'domain': domain}

    @api.onchange('product_id')
    def get_product_number(self):
        if self:
            if self.product_id:
                print(self.stock_production_lot_id)
                print(self.product_id.name)
                # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        # if self:
        #     print("1111111111")
        #     if self.needs_lots:
        #         print("22222222222")
        #         lot_id = self.env['stock.production.lot'].\
        #             search([('product_id.id', '=', self.product_id.id)], limit=1)
        #
        #         if lot_id:
        #             print("33333333")
        #             print(lot_id)
        #         print("444444444444")
                # self.stock_production_lot_id = lot_id.id
                # self.expiration_date = lot_id.life_date
        # print("55555555555555")


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    qty_per_liter = fields.Float('َQuantity In Liter', default=1)

    # @api.model
    # def _bom_find_domain(self, product_tmpl=None, product=None, picking_type=None, company_id=False, bom_type=False):
    #     if product:
    #         if not product_tmpl:
    #             product_tmpl = product.product_tmpl_id
    #         domain = ['|', ('product_id', '=', product.id), '&', ('product_id', '=', False),
    #                   ('product_tmpl_id', '=', product_tmpl.id)]
    #     elif product_tmpl:
    #         domain = [('product_tmpl_id', '=', product_tmpl.id)]
    #     else:
    #         # neither product nor template, makes no sense to search
    #         raise UserError(_('You should provide either a product or a product template to search a BoM'))
    #     if picking_type:
    #         domain += ['|', ('picking_type_id', '=', picking_type.id), ('picking_type_id', '=', False)]
    #     if company_id or self.env.context.get('company_id'):
    #         domain = domain + ['|', ('company_id', '=', False),
    #                            ('company_id', '=', company_id or self.env.context.get('company_id'))]
    #     if bom_type:
    #         domain += [('type', '=', 'phantom')]
    #     # order to prioritize bom with product_id over the one without
    #     return domain



# class MrpAbstractWorkorder(models.AbstractModel):
#     _inherit = "mrp.abstract.workorder"
#
#     def _update_finished_move(self):
#         """ Update the finished move & move lines in order to set the finished
#         product lot on it as well as the produced quantity. This method get the
#         information either from the last workorder or from the Produce wizard."""
#         print("testtttttttttttt")
#         production_move = self.production_id.move_finished_ids.filtered(
#             lambda move: move.product_id == self.product_id and
#             move.state not in ('done', 'cancel')
#         )
#         if production_move and production_move.product_id.tracking != 'none':
#             if not self.finished_lot_id:
#                 raise UserError(_('You need to provide a lot for the finished product.'))
#             move_line = production_move.move_line_ids.filtered(
#                 lambda line: line.lot_id.id == self.finished_lot_id.id
#             )
#             if move_line:
#                 if self.product_id.tracking == 'serial':
#                     raise UserError(_('You cannot produce the same serial number twice.'))
#                 move_line.product_uom_qty += self.qty_producing
#                 move_line.qty_done += self.qty_producing
#             else:
#                 location_dest_id = production_move.location_dest_id._get_putaway_strategy(self.product_id).id or production_move.location_dest_id.id
#                 move_line.create({
#                     'move_id': production_move.id,
#                     'product_id': production_move.product_id.id,
#                     'lot_id': self.finished_lot_id.id,
#                     'product_uom_qty': self.qty_producing,
#                     'product_uom_id': self.product_uom_id.id,
#                     'qty_done': self.qty_producing,
#                     'location_id': production_move.location_id.id,
#                     'location_dest_id': location_dest_id,
#                 })
        # else:
        #     rounding = production_move.product_uom.rounding
        #     production_move._set_quantity_done(
        #         float_round(self.qty_producing, precision_rounding=rounding)
        #     )



class MrpBomLines(models.Model):
    _name = 'mrp.bom.lines'

    name = fields.Char(string="Name")
    quantity = fields.Float(string="Quantity", default=1.0)
    actual_cost = fields.Float(string="Actual Cost", digits=(16, 4))
    total = fields.Float("Total",compute="_calc_total_extra", digits=(16, 4))
    mrp_id = fields.Many2one('mrp.production', 'MRP')
    bom_qty = fields.Float()
    qty_rate = fields.Float()

    @api.depends('actual_cost', 'quantity')
    def _calc_total_extra(self):
        if self:
            for rec in self:
                rec.total = rec.quantity * rec.actual_cost


class MRPBomExtra (models.Model):
    _inherit = 'mrp.bom.extra'

    # mrp_id = fields.Many2one('mrp.production', 'MRP')
    bom_qty = fields.Float(related='bom_id.product_qty')
    qty_rate = fields.Float(compute='_calc_qty_rate')

    @api.depends('bom_qty', 'quantity')
    def _calc_qty_rate(self):
        for rec in self:
            if rec.bom_qty and rec.quantity:
                rec.qty_rate = rec.quantity / rec.bom_qty


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"
    qty_per_liter = fields.Float('َQuantity In Liter', default=1)

    @api.onchange('qty_per_liter')
    def onchange_qty_per_liter(self):
        bom_obj = self.env['mrp.production'].browse(self.env.context.get('active_id'))
        if bom_obj:
            self.qty_producing = self.qty_per_liter * bom_obj.bom_id.product_qty


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    qty_to_produce_in_liter = fields.Float('Quantity In Liter', default=1)
    quality_check_id = fields.Many2one('quality.check')
    bom_extra_line_ids = fields.One2many('mrp.bom.lines', 'mrp_id', 'BoM Extra')

    @api.model
    def create(self, values):
        res = super(MrpProduction, self).create(values)
        res['origin'] = values['name']
        if res['move_raw_ids']:
            for line in res['move_raw_ids']:
                lot_id = self.env['stock.production.lot']. \
                                search([('product_id.id', '=', line.product_id.id)], limit=1)
                if lot_id:
                    line.stock_production_lot_id = lot_id.id
                    line.expiration_date = lot_id.life_date
        return res

    def open_produce_product(self):
        """ Save current wizard and directly opens a new. """
        res = super(MrpProduction, self).open_produce_product()
        res['context'] = {'default_qty_per_liter': self.qty_to_produce_in_liter}
        return res

    @api.onchange('bom_id')
    def onchange_bom_id(self):
        self.bom_extra_line_ids = False
        for line in self.bom_id.bom_extra_line_ids:
            self.bom_extra_line_ids.new({
                'mrp_id': self.id,
                'name': line.name,
                'quantity': line.quantity,
                'bom_qty': line.bom_qty,
                'qty_rate': line.qty_rate,
                'actual_cost': line.actual_cost,
            })

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self and self.bom_extra_line_ids:
            for i in self.bom_extra_line_ids:
                i.write({'quantity': i.qty_rate * self.product_qty})

    @api.onchange('qty_to_produce_in_liter')
    def onchange_qty_to_produce(self):
        if self.bom_id and self.bom_id.qty_per_liter > 0:
            self.product_qty = self.qty_to_produce_in_liter * self.bom_id.product_qty

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     self.product_qty = 30
    #     print(self.product_qty)
    #     res = super(MrpProduction, self).onchange_product_id()
    #     self.qty_to_produce_in_liter = self.bom_id.qty_per_liter
    #     self.product_qty = self.qty_to_produce_in_liter * self.bom_id.product_qty
    #     print(res)
    #     print(self.product_qty)
    #     return res
















    # @api.onchange('product_id', 'picking_type_id', 'company_id')
    # def onchange_product_id(self):
    #     print("111111111111")
    #     """ Finds UoM of changed product. """
    #     if not self.product_id:
    #         self.bom_id = False
    #     else:
    #         bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id,
    #                                             company_id=self.company_id.id)
    #         # , bom_type = 'normal'
    #         print("111111111111", bom)
    #         if bom:
    #             self.bom_id = bom.id
    #             self.product_qty = self.bom_id.product_qty
    #             self.product_uom_id = self.bom_id.product_uom_id.id
    #         else:
    #             self.bom_id = False
    #             self.product_uom_id = self.product_id.uom_id.id
    #         return {'domain': {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}
    #
    # @api.onchange('bom_id')
    # def _onchange_bom_id(self):
    #     self.product_qty = self.bom_id.product_qty
    #     self.product_uom_id = self.bom_id.product_uom_id.id
    #     print("xxxxxxxxxxxxxxxx: ", self.move_raw_ids)
    #     for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id):
    #         print(move, move.id)
    #     self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]
    #     print("yyyyyyyyyyyyyyyyyyy: ", self.move_raw_ids)
    #     self.picking_type_id = self.bom_id.picking_type_id or self.picking_type_id