from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salary = fields.Monetary(string='Salary')
    start_date = fields.Date(string='Start Date')
    retirement_date = fields.Date(string='Retirement Date')
    position_change_date = fields.Date(string='Position Change Date')
    end_date = fields.Date(string='End Date') 
    
    position_history_ids = fields.One2many(
        'hr.position.history',  
        'employee_id',          
        string="Position History",
        order='start_date desc, id desc'
    )

    current_position_history_id = fields.Many2one(
        'hr.position.history',
        compute='_compute_current_position',
        store=True
    )

    @api.depends('position_history_ids.start_date')
    def _compute_current_position(self):
        for rec in self:
            rec.current_position_history_id = rec.position_history_ids[:1] and rec.position_history_ids[0] or False

    @api.onchange('job_id', 'department_id', 'position_change_date')
    def _onchange_position_info(self):
        for rec in self:
            today = fields.Date.today()
            start = rec.position_change_date or today

            saved_recs = rec.position_history_ids.filtered(lambda r: r.id)
            new_recs = rec.position_history_ids.filtered(lambda r: not r.id)

            # ตรวจสอบว่ามี record ใหม่ซ้ำอยู่แล้วหรือไม่
            already_exists = any(
                r.job_id == rec.job_id and
                r.department_id == rec.department_id and
                r.start_date == start
                for r in new_recs
            )

            if not already_exists and (rec.job_id or rec.department_id):
                new_entry = self.env['hr.position.history'].new({
                    'job_id': rec.job_id.id,
                    'department_id': rec.department_id.id,
                    'start_date': start,
                    'end_date': rec.retirement_date or False,
                })

                # 👇 รวมทั้งหมดแล้วจัดเรียงจากใหม่ไปเก่า
                all_recs = new_entry + saved_recs + new_recs
                rec.position_history_ids = all_recs.sorted(
                    key=lambda r: r.start_date or today, reverse=True
                )
            else:
                # แค่ refresh เฉยๆ ไม่เพิ่มใหม่
                rec.position_history_ids = rec.position_history_ids.sorted(
                    key=lambda r: r.start_date or today, reverse=True
                )


