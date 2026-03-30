from odoo import models
import csv
import io
import base64

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def action_export_csv(self):

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Check In',
            'Check Out',
            'Employee Code',
            'Employee Name',
            'Email',
            'Phone',
            'Start Date',
            'Company',
            'Company Branch',
            'Department',
            'Travel Method',
            'Home-Work Distance (KM)',
        ])

        for rec in self:
            if not rec.check_in or not rec.check_out:
                continue

            employee = rec.employee_id

            travel_label = dict(
                employee._fields['travel_method'].selection
            ).get(employee.travel_method, '')

            writer.writerow([
                rec.check_in.strftime('%Y-%m-%d %H:%M:%S') if rec.check_in else '',
                rec.check_out.strftime('%Y-%m-%d %H:%M:%S') if rec.check_out else '',
                employee.employee_code or 'N/A',
                employee.name or 'Unknown User',
                employee.email or 'N/A',
                employee.phone or 'N/A',
                employee.start_date.strftime('%Y-%m-%d') if employee.start_date else 'N/A',
                employee.company_id.parent_id.name if employee.company_id.parent_id else 'Unknown Company',
                employee.company_id.name if employee.company_id  else 'Unknown Company Branch',
                employee.department_id.name if employee.department_id else 'N/A',
                travel_label,
                employee.distance_home_work or 0,
            ])

        file_data = base64.b64encode(output.getvalue().encode())

        attachment = self.env['ir.attachment'].create({
            'name': 'Attendance.csv',
            'type': 'binary',
            'datas': file_data,
            'res_model': 'hr.attendance',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }