from odoo import api, fields, models

class SkillCertification(models.Model):
    _inherit = 'hr.employee.skill'

    certification_file = fields.Binary(string="Certificate File")
    certification_filename = fields.Char(string="Filename")
    skill_certification_allowance = fields.Monetary(string='Skill Certification Allowance', currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
