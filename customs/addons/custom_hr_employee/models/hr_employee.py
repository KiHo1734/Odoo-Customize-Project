from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salary = fields.Monetary(string='Salary')
    start_date = fields.Date(string='Start Date')
    retirement_date = fields.Date(string='Retirement Date')
    position_change_date = fields.Date(string='Position Change Date')

    position_history = fields.One2many('hr.position.history', 'employee_id', string='Position History')
    end_date = fields.Date(string='End Date')
