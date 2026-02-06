from odoo import models, fields

class ShopfloorWork(models.Model):
    _name = 'shopfloor.work'
    _description = 'Shopfloor Work'

    workorder_id = fields.Many2one('mrp.workorder')
    employee_id = fields.Many2one('hr.employee')
    machine_id = fields.Many2one('mrp.workcenter')

    state = fields.Selection([
        ('ready', 'Ready'),
        ('working', 'Working'),
        ('pause', 'Pause'),
        ('done', 'Done'),
    ], default='ready')

    start_time = fields.Datetime()
    end_time = fields.Datetime()
