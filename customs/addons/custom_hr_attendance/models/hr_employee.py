from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    branch_id = fields.Many2one(
        'company.branch',
        string="Branch",
        default=lambda self: self.env.company.default_branch_id
    )   

    @api.model
    def create(self, vals):
        if not vals.get('branch_id'):
            vals['branch_id'] = self.env.company.default_branch_id.id
        return super().create(vals)