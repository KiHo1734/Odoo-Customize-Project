from odoo import fields, models

class EmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    employee_department_id = fields.Many2one(
        related='employee_id.department_id',
        string="Department",
        store=True,
        readonly=True,
    )


