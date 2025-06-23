from odoo import models, fields, api

class PositionHistory(models.Model):
    _name = 'hr.position.history'
    _description = 'Position History'

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    job_id = fields.Many2one('hr.job', string='Position')
    start_date = fields.Date(string='Start Date')
    department_id = fields.Many2one('hr.department', string='Department')
    end_date = fields.Date(string='End Date')
    description = fields.Text(string='Description')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.employee_id:
            res.employee_id.job_id = res.job_id
            res.employee_id.department_id = res.department_id
            res.employee_id.position_change_date = res.start_date
            res.employee_id.end_date = res.end_date 
        return res
