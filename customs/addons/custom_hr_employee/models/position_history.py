from odoo import models, fields, api

class PositionHistory(models.Model):
    _name = 'hr.position.history'
    _description = 'Position History'

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, required=True)
    job_id = fields.Many2one('hr.job', string='Position')
    start_date = fields.Date(string='Start Date', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    end_date = fields.Date(string='End Date')
    description = fields.Text(string='Description')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:  
            if rec.employee_id:
                rec.employee_id.job_id = rec.job_id
                rec.employee_id.department_id = rec.department_id
                rec.employee_id.position_change_date = rec.start_date
                rec.employee_id.end_date = rec.end_date
        return res
