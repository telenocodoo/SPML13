from odoo import models, fields, api,_
from odoo.exceptions import AccessError, UserError
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare

class BankAccount(models.Model):
    _inherit = 'account.bank.statement.line'

    bank_account = fields.Many2one('account.account', 'Account')
    employee_name = fields.Many2one('hr.employee', 'Employee')


class Manufactoring(models.Model):
    _inherit = 'mrp.production'

    extra_costs = fields.One2many('extra.cost', 'raw_material_extra')

    #magdy
    def calculate_scrap_cost(self):
        component_cost = 0.0
        extra_cost = 0.0
        extra_component = 0.0
        number_of_scraped_unit = 0.0
        scrap_id = self.env['stock.scrap'].search([('production_id', '=', self.id)])
        if scrap_id:
            for s in scrap_id:
                number_of_scraped_unit += s.scrap_qty

        for c in self.move_raw_ids:
            print("c.quantity_done", c.quantity_done)
            print("c.product_id.standard_price", c.product_id.standard_price)
            component_cost += c.quantity_done * c.product_id.standard_price
        for i in self.extra_costs:
            extra_cost += i.cost_extra
        for ex in self.bom_extra_line_ids:
            extra_component += ex.total

        unit_cost_before_scrap = (component_cost + extra_cost + extra_component) / self.product_qty
        total_cost_of_scrap = unit_cost_before_scrap * number_of_scraped_unit
            # if number_of_scraped_unit > 0 else unit_cost_before_scrap
        remaining_unit = self.product_qty - number_of_scraped_unit
        unit_extra_cost_of_scrap = total_cost_of_scrap / remaining_unit if remaining_unit>0 else total_cost_of_scrap
        final_unit = unit_extra_cost_of_scrap + unit_cost_before_scrap
        return {
            'unit_cost_before_scrap': unit_cost_before_scrap,
            'total_cost_of_scrap': total_cost_of_scrap,
            'remaining_unit': remaining_unit,
            'unit_extra_cost_of_scrap': unit_extra_cost_of_scrap,
            'final_unit': final_unit,
        }


class ExtraCosts(models.Model):
    _name = 'extra.cost'

    raw_material_extra = fields.Many2one('mrp.production', string='Name')
    name_extra = fields.Char(string='Name')
    cost_extra = fields.Float(string='Extra Cost')


class MrpCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'
    _description = 'MRP Cost Structure Report'

    def get_lines(self, productions):
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        stock_scrap_obj = self.env['stock.scrap']


        res = []
        docs = []
        # magdy
        ex_component = []
        extra_cost = 0.0

        cost=[]

        print("production",productions.calculate_scrap_cost())
        print("production",productions)
        for product in productions.mapped('product_id'):
            mos = productions.filtered(lambda m: m.product_id == product)
            print("product",product)
            total_cost = 0.0
            mrpproduct = self.env['mrp.production'].search([('id', '=', mos.id)])
            # print(mrpproduct.name)
            total_cost = 0.0
            for i in mrpproduct.extra_costs:
                extra_cost = extra_cost + i.cost_extra
                docs.append({
                    'name_extra': i.name_extra,
                    'cost_extra': i.cost_extra,
                })

            #magdy
            for ex in mrpproduct.bom_extra_line_ids:
                # extra_cost = extra_cost + i.cost_extra
                ex_component.append({
                    'name': ex.name,
                    'quantity': ex.quantity,
                    'actual_cost': ex.actual_cost,
                    'total': ex.total,
                })


            #get the cost of operations
            operations = []
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            print("Workorders",Workorders)
            if Workorders:
                query_str = """SELECT w.operation_id, op.name, partner.name, sum(t.duration), wc.costs_hour
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                LEFT JOIN res_users u ON (t.user_id = u.id)
                                LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
                                LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                                GROUP BY w.operation_id, op.name, partner.name, t.user_id, wc.costs_hour
                                ORDER BY op.name, partner.name
                            """
                self.env.cr.execute(query_str, (tuple(Workorders.ids), ))
                for op_id, op_name, user, duration, cost_hour in self.env.cr.fetchall():
                    operations.append([user, op_id, op_name, duration / 60.0, cost_hour])

            #get the cost of raw material effectively used
            raw_material_moves = []
            query_str = """SELECT sm.product_id, sm.bom_line_id, abs(SUM(svl.quantity)), abs(SUM(svl.value))
                             FROM stock_move AS sm
                       INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                            WHERE sm.raw_material_production_id in %s AND sm.state != 'cancel' AND sm.product_qty != 0 AND scrapped != 't'
                         GROUP BY sm.bom_line_id, sm.product_id"""
            self.env.cr.execute(query_str, (tuple(mos.ids), ))
            for product_id, bom_line_id, qty, cost in self.env.cr.fetchall():
                raw_material_moves.append({
                    'qty': qty,
                    'cost': cost,
                    'product_id': ProductProduct.browse(product_id),
                    'bom_line_id': bom_line_id
                })
                total_cost += cost

            #get the cost of scrapped materials
            # scraps = StockMove.search([('production_id', 'in', mos.ids), ('scrapped', '=', True), ('state', '=', 'done')])
            #magdy
            scraps = stock_scrap_obj.search([('production_id', 'in', mos.ids), ('state', '=', 'done')])
            #magdy
            uom = mos and mos[0].product_uom_id
            mo_qty = 0
            if not all(m.product_uom_id.id == uom.id for m in mos):
                uom = product.uom_id
                for m in mos:
                    qty = sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))
                    if m.product_uom_id.id == uom.id:
                        mo_qty += qty
                    else:
                        mo_qty += m.product_uom_id._compute_quantity(qty, uom)
            else:
                for m in mos:
                    mo_qty += sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))


            for m in mos:
                byproduct_moves = m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id != product)
            # magdy
            res.append({
                'product': product,
                'mo_qty': mo_qty,
                'mo_uom': uom,
                'operations': operations,
                'currency': self.env.company.currency_id,
                'raw_material_moves': raw_material_moves,
                'total_cost': total_cost,
                'scraps': scraps,
                # 'name_extra': i.name_extra,
                'ex_component': ex_component,
                'scrap_cost': productions.calculate_scrap_cost(),
                'docs': docs,
                'mocount': len(mos),
                'byproduct_moves': byproduct_moves,
                'extra_cost': extra_cost

            })

            print(res)
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        productions = self.env['mrp.production']\
            .browse(docids)\
            .filtered(lambda p: p.state != 'cancel')
        res = None
        if all([production.state == 'done' for production in productions]):
            res = self.get_lines(productions)
        return {'lines': res}


class ProductTemplateCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.product_template_cost_structure'
    _description = 'Product Template Cost Structure Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        productions = self.env['mrp.production'].search([('product_id', 'in', docids), ('state', '=', 'done')])
        res = self.env['report.mrp_account_enterprise.mrp_cost_structure'].get_lines(productions)
        return {'lines': res}

class MRPMaterial(models.Model):

    _inherit = 'mrp.production'
    _description = 'MRP Raw Material'

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search([('name', '=', 'QC/Scrap')], limit=1).id

    def _get_default_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search(
            [('name', '=', 'My Company: Scrap'), ('location_id.name', '=', 'Virtual Locations')], limit=1).id

    # state = fields.Selection(selection_add=[('raw', 'Request Raw Material'),('qc', 'Failed/Scrap'),('transfer', 'QC Check')])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('transfer', 'QC Check'),
        ('qc', 'Failed/Scrap'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * Planned: The WO are planned.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
    src_location_id=fields.Many2one('stock.location', 'QC location',  default=_get_default_scrap_location_id,
        )

    scrap_location_id = fields.Many2one('stock.location', 'Scrap location',
                                                   default=_get_default_location_id)
    qc_boolean = fields.Boolean(default=False)

    def action_request(self):
        dropship_vals = []
        # print("HEllo")
        self.write({'state': 'raw'})
        for company in self:
            location_id = self.env['stock.location'].search([('usage', '=', 'production')],limit=1)
            # location_id = self.env['stock.location'].search([('location_id.name', '=', 'Virtual Locations')])

            src_location_id = self.env['stock.location'].search([('name', '=', 'Stock'),('usage', '=', 'internal'),('location_id.name', '=', 'WH')],limit=1)
            for i in src_location_id:
                print(i.location_id.name)

            # print("src_location_id.name",src_location_id.name)
            sequence = self.env['ir.sequence'].search([
                ('code', '=', 'stock.dropshipping')])
            dropship_picking_type = self.env['stock.picking.type'].search([
                ('name', '=', 'Request Raw Material')], limit=1)

            product_car = self.env['product.product'].search([
                ('id', '=', company.product_id.id)], limit=1)

            dropship_vals.append({
                'name': 'Request Raw Material',
                'warehouse_id':self.env.user.company_id.id,
                'sequence_id': sequence.id,
                'code': 'internal',
                'default_location_src_id': src_location_id.id,
                'default_location_dest_id': location_id.id,
                'sequence_code': 'RRM',

            })
            if not dropship_picking_type:
                print("Inside")


                self.env['stock.picking.type'].create(dropship_vals)
                dropship_picking_type = self.env['stock.picking.type'].search([
                    ('name', '=', 'Request Raw Material')], limit=1)
                picking = self.env['stock.picking'].create({
                    'location_id': src_location_id.id,
                    'location_dest_id': location_id.id,
                    'partner_id': self._uid,
                    'origin': self.origin,
                    'picking_type_id': dropship_picking_type.id,
                    'immediate_transfer': True,

                })
                print(picking)
                for i in company.move_raw_ids:
                    # print(i.product_id.name)

                    move_receipt_1 = self.env['stock.move'].create({
                        'name': i.name,
                        'product_id': i.product_id.id,
                        'product_uom_qty': i.product_qty,
                        'quantity_done': company.product_qty,
                        'product_uom': i.product_id.uom_id.id,
                        'picking_id': picking.id,
                        'picking_type_id': dropship_picking_type.id,
                        'location_id': src_location_id.id,
                        'location_dest_id': location_id.id,
                    })
                    picking.action_confirm()

            else:
                print("else")
                location_id = self.env['stock.location'].search([('usage', '=', 'production')],limit=1)
                # print(dropship_picking_type.name)
                picking = self.env['stock.picking'].create({
                    'location_id': src_location_id.id,
                    'location_dest_id': location_id.id,
                    'partner_id': self._uid,
                    'origin': self.origin,
                    'picking_type_id': dropship_picking_type.id,
                    'immediate_transfer': True,
                })
                for i in company.move_raw_ids:
                    # print(i.product_id.name)

                    move_receipt_1 = self.env['stock.move'].create({
                        'name': i.name,
                        'product_id': i.product_id.id,
                        'product_uom_qty': i.product_qty,
                        'quantity_done': company.product_qty,
                        'product_uom': i.product_id.uom_id.id,
                        'picking_id': picking.id,
                        'picking_type_id': dropship_picking_type.id,
                        'location_id': src_location_id.id,
                        'location_dest_id': location_id.id,
                    })
                    # print(move_receipt_1)
                    # move_line_paw = self.env['stock.move.line'].create({
                    #     'product_id': i.product_id.id,
                    #     'product_uom_id': i.product_id.uom_id.id,
                    #     'picking_id': picking.id,
                    #     'qty_done': company.product_qty,
                    #     'location_id': self.env.ref('stock.stock_location_suppliers').id,
                    #     'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    # })
                    # print('l',l)
                    picking.action_confirm()

    def button_qc_sample(self):
        self.ensure_one()
        # self.write({'state': 'qc'})
        # src_location_id = self.env['stock.location'].search([('name', '=', 'YourCompany: QC/Scrap'),('location_id.name', '=', 'Virtual Locations')], limit=1)
        print("src_location_id",self.src_location_id.name)
        self.qc_boolean = True


        return {
            'name': _('QC Sample'),
                'view_mode': 'form',
                'res_model': 'stock.scrap',
                'view_id': self.env.ref('stock.stock_scrap_form_view2').id,
                'type': 'ir.actions.act_window',
                'context': {'default_production_id': self.id,
                             'default_product_id': self.product_id.id,
                            'product_ids': (self.finished_move_line_ids.filtered(lambda x: x.state not in ('done', 'cancel'))).mapped(
                    'product_id').ids,
                            },
                'target': 'new',
            }

    def button_scrap(self):
        # self.ensure_one()
        self.qc_boolean = False
        print("scrap_location_id",self.scrap_location_id.name)
        print("::::::::::::::::::::::::::::",self.location_dest_id.name)
        return {
            'name': _('Scrap'),
            'view_mode': 'form',
            'res_model': 'stock.scrap',
            'view_id': self.env.ref('stock.stock_scrap_form_view2').id,
            'type': 'ir.actions.act_window',
            'context': {'default_production_id': self.id,
                         'default_product_id': self.product_id.id,
                        'product_ids': (self.finished_move_line_ids.filtered(lambda x: x.state not in ('done', 'cancel'))).mapped(
                'product_id').ids,
                        },
            'target': 'new',
        }


    def action_internal(self):
        values_to_create = []
        active_id = self.id
        print("active_id",active_id)
        self.write({'state': 'transfer'})

        for production in self:
            points = self.env['quality.point'].search([('title', '=', 'RRM Quality Points')],limit=1)
            if points:
                points = self.env['quality.point'].search([('title','=','RRM Quality Points')],limit=1)
                picking_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'RRM')],limit=1)
                test_type_id = self.env['quality.point.test_type'].search([('name', '=', 'Pass - Fail')])
                team_id = self.env['quality.alert.team'].search([('name', '=', 'Main Quality Team')])
                name = self.name
                picking_id = self.env['stock.picking'].search([('origin', '=', self.origin)],limit=1)
                quality_check_data = {
                    'picking_id': picking_id.id,
                    'product_id': self.product_id.id,
                    'point_id': points.id,
                    'company_id': self.company_id.id,
                    'team_id': team_id.id,
                    'test_type_id': test_type_id.id,
                    'origin': self.origin,
                }
                k = self.env['quality.check'].create(quality_check_data)
                self.quality_check_id = k.id
            else:
                picking_type_id=self.env['stock.picking.type'].search([('sequence_code','=','RRM')],limit=1)
                test_type_id = self.env['quality.point.test_type'].search([('name','=','Pass - Fail')])

                l=self.env['quality.point'].create({
                    'product_id': self.product_id.id,
                    'product_tmpl_id': self.product_id.product_tmpl_id.id,
                    'title': "RRM Quality Points",
                    'picking_type_id': picking_type_id.id,
                    'test_type_id': test_type_id.id
                })

                team_id = self.env['quality.alert.team'].search([('name', '=', 'Main Quality Team')])

                name=self.name
                picking_id = self.env['stock.picking'].search([('origin', '=', self.origin)],limit=1)

                quality_check_data = {
                    'picking_id': picking_id.id,
                    'product_id': self.product_id.id,
                    'point_id':points.id,
                    'company_id': self.company_id.id,
                    'team_id': team_id.id,
                    'test_type_id': test_type_id.id,
                    'origin': self.origin,
                }
                k=self.env['quality.check'].create(quality_check_data)
                self.quality_check_id = k.id



    def action_pass(self):
        print("Hello")

        scrapobj = self.env['stock.scrap'].search(
            [('production_id', '=', self.id), ('product_id', '=', self.product_id.id)])

        location_id = self.env['stock.location'].search([('name', '=', 'Finished Good')], limit=1)
        src_location_id = self.env['stock.location'].search(
            [('name', '=', 'Stock'), ('usage', '=', 'internal'), ('location_id.name', '=', 'WH')], limit=1)

        total = 0
        for i in scrapobj:
            total = total + i.scrap_qty
        for company in self:
            self.write({'state': 'transfer'})
            picking = self.env['stock.picking'].create({
                'location_id': location_id.id,
                'location_dest_id': src_location_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                'origin': self.origin,
            })
            for i in company:
                move_receipt_1 = self.env['stock.move'].create({
                    'name': i.name,
                    'product_id': i.product_id.id,
                    'product_uom_qty': company.product_qty - total,
                    'quantity_done': company.product_qty - total,
                    'product_uom': i.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                    'location_id': location_id.id,
                    'location_dest_id': src_location_id.id,
                })
                print(" move_receipt_1",move_receipt_1['product_uom_qty'])
                k=self.env['stock.move.line'].create({
                    'move_id': move_receipt_1.id,
                    'picking_id': move_receipt_1.picking_id.id,
                    'product_id': move_receipt_1.product_id.id,
                    'location_id': move_receipt_1.location_id.id,
                    'location_dest_id': move_receipt_1.location_dest_id.id,
                    'product_uom_qty': company.product_qty - total,
                    'product_uom_id':move_receipt_1.product_id.uom_id.id,
                    'qty_done': company.product_qty - total,
                })

            picking.action_confirm()

# magdy
    def button_mark_done(self):
            sequence = self.env['quality.check'].search([('origin', '=', self.origin)], limit=1)
            print(sequence.origin)
            if sequence.quality_state in ['pass']:
                self.ensure_one()
                self.action_pass()
                self._check_company()
                for wo in self.workorder_ids:
                    if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                        raise UserError(_('Work order %s is still running') % wo.name)
                self._check_lots()

                self.post_inventory()
                # Moves without quantity done are not posted => set them as done instead of canceling. In
                # case the user edits the MO later on and sets some consumed quantity on those, we do not
                # want the move lines to be canceled.
                (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
                    'state': 'done',
                    'product_uom_qty': 0.0,
                })
                return self.write({'date_finished': fields.Datetime.now()})

            else:
                raise UserError(_("First process the quality check."))
#
# magdy


    # def post_inventory(self):
    #     sequence = self.env['quality.check'].search([('origin', '=', self.origin)], limit=1)
    #     print(sequence.origin)
    #     self.action_pass()
    #     if sequence.quality_state in ['pass']:
    #         for order in self:
    #             moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
    #             moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             print("moves_to_do",moves_to_do)
    #             for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
    #                 move.product_uom_qty = move.quantity_done
    #                 print("move.product_uom_qty",move.product_uom_qty)
    #             # MRP do not merge move, catch the result of _action_done in order
    #             # to get extra moves.
    #             moves_to_do = moves_to_do._action_done()
    #             moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
    #             order._cal_price(moves_to_do)
    #             moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             moves_to_finish = moves_to_finish._action_done()
    #             order.workorder_ids.mapped('raw_workorder_line_ids').unlink()
    #             order.workorder_ids.mapped('finished_workorder_line_ids').unlink()
    #             order.action_assign()
    #             consume_move_lines = moves_to_do.mapped('move_line_ids')
    #             for moveline in moves_to_finish.mapped('move_line_ids'):
    #                 if moveline.move_id.has_tracking != 'none' and moveline.product_id == order.product_id or moveline.lot_id in consume_move_lines.mapped('lot_produced_ids'):
    #                     if any([not ml.lot_produced_ids for ml in consume_move_lines]):
    #                         raise UserError(_('You can not consume without telling for which lot you consumed it'))
    #                     # Link all movelines in the consumed with same lot_produced_ids false or the correct lot_produced_ids
    #                     filtered_lines = consume_move_lines.filtered(lambda ml: moveline.lot_id in ml.lot_produced_ids)
    #                     moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
    #                 else:
    #                     # Link with everything
    #                     moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
    #         return True
    #
    #     else:
    #
    #             raise UserError(_("First process the Quality Check."))


# magdy
#     def action_confirm(self):
#         sequence = self.env['stock.picking'].search([
#             ('origin', '=', self.origin)],limit=1)
#         print(sequence.origin)
#
#         if sequence.state in ['done']:
#             self._check_company()
#             for production in self:
#                 if not production.move_raw_ids:
#                     raise UserError(_("Add some materials to consume before marking this MO as to do."))
#                 for move_raw in production.move_raw_ids:
#                     move_raw.write({
#                         'group_id': production.procurement_group_id.id,
#                         'unit_factor': move_raw.product_uom_qty / production.product_qty,
#                         'reference': production.name,  # set reference when MO name is different than 'New'
#                     })
#                 production._generate_finished_moves()
#                 production.move_raw_ids._adjust_procure_method()
#                 (production.move_raw_ids | production.move_finished_ids)._action_confirm()
#             return True
#         else:
#             raise UserError(_("Request for Raw Material is not Validated yet."))
# magdy




class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    @api.onchange('company_id')
    def _onchange_company_id(self):
        res = super(StockScrap, self)._onchange_company_id()
        if self.env.context.get('active_model') == 'mrp.production':
            request_id = self.env.context.get('active_ids', False)

            m = self.env['mrp.production'].browse(request_id[0])
            if m.qc_boolean == True:
                self.location_id = m.location_dest_id.id
                self.scrap_location_id = m.src_location_id.id
            else:
                self.location_id = m.location_dest_id.id
                self.scrap_location_id = m.scrap_location_id.id

        else:
            if self.company_id:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
                self.location_id = warehouse.lot_stock_id
                self.scrap_location_id = self.env['stock.location'].search([
                    ('scrap_location', '=', True),
                    ('company_id', 'in', [self.company_id.id, False]),
                ], limit=1)
            else:
                self.location_id = False
                self.scrap_location_id = False

        return res


    # location_id = fields.Many2one('stock.location', 'Source Location')
    # scrap_location_id = fields.Many2one('stock.location', 'Scrap Location')

class QualityCheck(models.Model):
    _inherit = "quality.check"

    origin=fields.Char("Source")

    def do_fail(self):
        res = super(QualityCheck, self).do_fail()
        mrpobj = self.env['mrp.production'].search([('origin', '=', self.origin)],limit=1)
        picking_id = self.env['stock.picking'].search([('origin', '=', self.origin)], limit=1)
        mrpobj.state='qc'
        mrpobj.action_see_move_scrap()
        print(mrpobj.picking_type_id.name)
        self.write({
            'quality_state': 'fail',
            'user_id': self.env.user.id,
            'control_date': datetime.now()})
        self.redirect_after_pass_fail()
        # picking.button_scrap()
        # scrap = self.env['stock.scrap'].create({
        #     'product_id': self.product_id.id,
        #     'product_uom_id': self.product_id.uom_id.id,
        #     'scrap_qty': mrpobj.product_qty,
        #     'origin': self.origin,
        #     'picking_id': picking_id.id,
        #     'state':'done'
        # })

        dropship_picking_type = self.env['stock.picking.type'].search([
            ('name', '=', 'Request Raw Material')], limit=1)
        picking = self.env['stock.picking'].create({
            'location_id': mrpobj.location_dest_id.id,
            'location_dest_id': mrpobj.src_location_id.id,
            'partner_id': self._uid,
            'origin': self.origin,
            'picking_type_id': dropship_picking_type.id,
            'immediate_transfer': True,

        })
        print(picking)
        for i in mrpobj.move_raw_ids:
            # print(i.product_id.name)

            move_receipt_1 = self.env['stock.move'].create({
                'name': i.name,
                'product_id': i.product_id.id,
                'product_uom_qty': i.product_qty,
                'quantity_done': mrpobj.product_qty,
                'product_uom': i.product_id.uom_id.id,
                'picking_id': picking.id,
                'picking_type_id': dropship_picking_type.id,
                'location_id': mrpobj.location_dest_id.id,
                'location_dest_id': mrpobj.src_location_id.id,
            })
            picking.action_confirm()
            picking.button_validate()
            picking.button_scrap()

            self.env['stock.move.line'].create({
                'move_id': move_receipt_1.id,
                # 'lot_id': move_line.lot_id.id,
                'qty_done': i.product_qty,
                'product_id': i.product_id.id,
                'product_uom_id': i.product_id.uom_id.id,
                'location_id': mrpobj.location_dest_id.id,
                'location_dest_id': mrpobj.src_location_id.id,
                'state': 'done',
            })

        # scrap.sudo().action_validate()
        return res


    def do_pass(self):
        mrpobj = self.env['mrp.production'].search([('origin', '=',self.origin)],limit=1)

        print("mrpobj",mrpobj.origin)



        self.write({'quality_state': 'pass',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        mrpobj.button_mark_done()
        return self.redirect_after_pass_fail()



