from odoo import models, fields

class PositionHistory(models.Model):
    _name = 'hr.position.history'
    _description = 'Employee Position History'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    job_id = fields.Many2one('hr.job', string='Job Position')
    department_id = fields.Many2one('hr.department', string='Department')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    note = fields.Text(string='Notes')
