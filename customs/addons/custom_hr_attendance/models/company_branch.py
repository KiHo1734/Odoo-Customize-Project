from odoo import models, fields, api

class CompanyBranch(models.Model):
    _name = 'company.branch'
    _description = 'Company Branch'

    name = fields.Char(string="Branch Name", required=True)
    code = fields.Char(string="Branch Code")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        branch = super().create(vals)

        employees = self.env['hr.employee'].search([
            ('company_id', '=', branch.company_id.id)
        ])
        employees.write({'branch_id': branch.id})

        return branch

class ResCompany(models.Model):
    _inherit = 'res.company'

    branch_ids = fields.One2many(
        'company.branch',
        'company_id',
        string="Branches"
    )

    default_branch_id = fields.Many2one(
        'company.branch',
        string="Default Branch"
    )

    def write(self, vals):
        res = super().write(vals)

        if 'default_branch_id' in vals:
            for company in self:
                employees = self.env['hr.employee'].search([
                    ('company_id', '=', company.id)
                ])
                employees.write({
                    'branch_id': company.default_branch_id.id
                })

        return res