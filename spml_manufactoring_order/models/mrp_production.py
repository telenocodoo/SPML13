# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    mrp_production_id = fields.Many2one(comodel_name="mrp.production")
    test_line_ids = fields.One2many("quality.test.lines", "quality_test_id")
    analyzed_by_id = fields.Many2one("res.users")
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    no_of_sterility = fields.Float()
    no_of_colonies = fields.Float()
    is_pass = fields.Boolean(compute='get_pass_value', default=False, store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if self.test_line_ids:
                self.test_line_ids=False
            old_lines = self.env['quality.check.test'].search([('product_id', '=', self.product_id.id)])
            if old_lines:
                for record in old_lines:
                    for line in record.quality_test_ids:
                        res = {
                                # 'quality_test_id': self.id,
                                'question_id': line.question_id.id,
                                'question_type': line.question_type,
                                'q_from': line.q_from,
                                'q_to': line.q_to,
                                'specification': line.specification,
                                'is_success': line.is_success,
                            }
                        self.update({
                            'test_line_ids': [(0, 0, res)],
                        })
                        # new_lines.new(res)

    @api.depends('test_line_ids')
    def get_pass_value(self):
        for record in self:
            for line in record.test_line_ids:
                if line.is_success == False:
                    record.is_pass = False
                    break
                else:
                    record.is_pass = True

    def do_pass(self):
        if self.is_pass == False:
            raise UserError(_("Please review your Quality Tests result"))
        res = super(QualityCheck, self).do_pass()
        self.mrp_production_id.button_mark_done()
        return res


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    state = fields.Selection(selection_add=[('test', 'Testing')])
#     state = fields.Selection([
#         ('confirmed', 'Confirmed'),
#         ('planned', 'Planned'),
#         ('progress', 'In Progress'),
#         ('test', 'Testing'),
#         ('done', 'Done'),
#         ('cancel', 'Cancelled')], string='State',
#         copy=False, default='confirmed', track_visibility='onchange')

    # @api.multi
    def button_check_testing(self):
        team_id = self.env['quality.alert.team'].search([])[0]
        quality_test_type_id = self.env['quality.point.test_type'].search([])[0]
        print(team_id)
        print(quality_test_type_id)
        qc_id = self.env['quality.check'].create(
            {
                'product_id': self.product_id.id,
                'mrp_production_id': self.id,
                'team_id': team_id.id,
                'test_type_id': quality_test_type_id.id if quality_test_type_id else False,
            }
        )
        print(qc_id)
        qc_id.test_line_ids = False
        old_lines = self.env['quality.check.test'].search([('product_id', '=', self.product_id.id)])
        new_lines = self.env['quality.test.lines']
        if old_lines:
            print("11111111111")
            for record in old_lines:
                print("1111111111122222222222")
                for line in record.quality_test_ids:
                    print("11111111111333333333333333")
                    res = {
                            'quality_test_id': qc_id.id,
                            'question_id': line.question_id.id,
                            'question_type': line.question_type,
                            'q_from': line.q_from,
                            'q_to': line.q_to,
                            'specification': line.specification,
                        }
                    print("1111111111144444444444444")
                    new_lines.create(res)
        print("11111111111555555555555555555555")
        self.write({'state': 'test'})

