from odoo import api, models, fields

class HrRetirementReportWizard(models.TransientModel):
    _name = 'hr.retirement.report.wizard'
    _description = 'Retirement Report Wizard'

    date_from = fields.Date(string="จากวันที่")
    date_to = fields.Date(string="ถึงวันที่")
    employee_ids = fields.Many2many('hr.employee', string="พนักงาน")

    def print_report(self):
        self.ensure_one()
        domain = []
        
        # ถ้ามีการระบุวันที่
        if self.date_from:
            domain.append(('retirement_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('retirement_date', '<=', self.date_to))

        # ค้นหาพนักงานตามเงื่อนไข
        if domain:
            employees = self.env['hr.employee'].search(domain)
        else:
            # ถ้าไม่มีเงื่อนไขวันที่ ให้ใช้พนักงานที่เลือกมา
            employees = self.employee_ids or self.env['hr.employee'].browse(self._context.get('active_ids', []))

        data = {
            'form': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else '',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else '',
                'employee_ids': employees.ids,
            }
        }
        
        return self.env.ref('custom_hr_employee.action_report_retirement_employee_list').report_action(self, data=data)
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if data and data.get('form'):
            employee_ids = self.env['hr.employee'].browse(data.get('form', {}).get('employee_ids', []))
        else:
            employee_ids = self.env['hr.employee'].browse(docids)

        # อัปเดต leave และ absence ก่อน render
        # ก่อนส่งรายงาน
        for emp in employee_ids:
            emp._compute_leave_days(start_date=self.date_from, end_date=self.date_to)
            emp._compute_absence_days(start_date=self.date_from, end_date=self.date_to)

        return {
            'doc_ids': employee_ids.ids,
            'doc_model': 'hr.employee',
            'docs': employee_ids,
            'form': data.get('form', {}) if data else {},
            'employee_ids': employee_ids,
        }

class ReportRetirementEmployeeList(models.AbstractModel):
    _name = 'report.custom_hr_employee.report_employee_list_template'
    _description = 'Retirement Employee List Report'

    def _get_report_values(self, docids, data=None):
        if data and data.get('form'):
            employee_ids = self.env['hr.employee'].browse(data.get('form', {}).get('employee_ids', []))
        else:
            employee_ids = self.env['hr.employee'].browse(docids)
            
        return {
            'doc_ids': employee_ids.ids,
            'doc_model': 'hr.employee',
            'docs': employee_ids,
            'form': data.get('form', {}) if data else {},
            'employee_ids': employee_ids,
        }