import datetime
from odoo import models, fields, api
from ThaiPersonalCardExtract import PersonalCard
from ThaiPersonalCardExtract.utils import Language
import base64
import tempfile
from odoo.exceptions import UserError
import unicodedata
from cryptography.fernet import Fernet

class HrPersonalCardExtract(models.Model):
    _inherit = 'hr.employee'

    id_card_image = fields.Binary(string='ID Card Image', attachment=False)
    religion = fields.Char(string="Religion")

    identification_id_encrypted = fields.Char(store=True)

    identification_id = fields.Char(
        string="ID Number",
        compute="_compute_identification_id",
        inverse="_inverse_identification_id",
        store=False,
    )

    # read เป็น function พื้นฐานของ odoo ที่จะเรียกใช้อัติโนมัติ โดยในส่วนจะใช้สำหรับการ Decryption
    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields, load)
        if not fields or 'identification_id' in fields:
            for record, val in zip(self, res):
                if record.identification_id_encrypted:
                    try:
                        fernet = record._get_or_create_fernet()
                        val['identification_id'] = fernet.decrypt(record.identification_id_encrypted.encode()).decode()
                    except Exception:
                        val['identification_id'] = False
        return res


    def _get_or_create_fernet(self):
        Param = self.env['ir.config_parameter'].sudo()
        key = Param.get_param('personal_card_fernet_key')
        if not key:
            key = Fernet.generate_key().decode()
            Param.set_param('personal_card_fernet_key', key)
        return Fernet(key.encode())
    
    @api.depends('identification_id_encrypted')
    def _compute_identification_id(self):
        for rec in self:
            if rec.identification_id_encrypted:
                try:
                    fernet = rec._get_or_create_fernet()
                    rec.identification_id = fernet.decrypt(rec.identification_id_encrypted.encode()).decode()
                except:
                    rec.identification_id = False
            else:
                rec.identification_id = False

    def _inverse_identification_id(self):
        for rec in self:
            if rec.identification_id:
                fernet = rec._get_or_create_fernet()
                rec.identification_id_encrypted = fernet.encrypt(rec.identification_id.encode()).decode()
            else:
                rec.identification_id_encrypted = False

    @api.onchange('id_card_image')
    def _onchange_id_card_image(self):
        if self.id_card_image:
            self._extract_from_image_single()

    @api.model
    def _get_tesseract_cmd(self):
        return r"D:\Anaconda\tesseractOCR\tesseract.exe"

    def extract_info_from_image(self):
        for rec in self:
            rec._extract_from_image_single()

    @staticmethod
    def thai_date_to_date(date_str):
        thai_months = {
            'ม.ค': '01', 'ก.พ': '02', 'มี.ค': '03', 'เม.ย': '04',
            'พ.ค': '05', 'มิ.ย': '06', 'ก.ค': '07', 'ส.ค': '08',
            'ก.ย': '09', 'ต.ค': '10', 'พ.ย': '11', 'ธ.ค': '12',
            'มี.ย': '06'
        }

        try:
            # Normalize ช่องว่างและอักขระพิเศษ
            date_str = unicodedata.normalize("NFKC", date_str).replace('\u00a0', ' ').strip()
            parts = date_str.split()

            if len(parts) != 3:
                print(f"❌ รูปแบบไม่ถูกต้อง: {parts}")
                return None

            day = parts[0]
            raw_month = parts[1].replace(".", "")  # ลบจุดจากชื่อเดือน เช่น "มี.ย." -> "มี.ย" -> "มีค"
            year = int(parts[2]) - 543

            # ลอง map เดือนอีกครั้ง
            for key in thai_months:
                if raw_month in key.replace(".", ""):
                    month = thai_months[key]
                    break
            else:
                print(f"❌ ไม่รู้จักเดือน: '{raw_month}'")
                return None

            return datetime.datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None


    def _extract_from_image_single(self):
        if not self.id_card_image:
            raise UserError("กรุณาอัปโหลดรูปบัตรประชาชนก่อน")

        image_data = base64.b64decode(self.id_card_image)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_data)
            temp_path = f.name

        try:
            reader = PersonalCard(
                lang=Language.MIX,
                tesseract_cmd=self._get_tesseract_cmd()
            )
            
            result = reader.extract_front_info(temp_path)

            id_number = getattr(result, "card_id", result.Identification_Number)
            fernet = self._get_or_create_fernet()
            self.identification_id_encrypted = fernet.encrypt(id_number.encode()).decode()

            self.name = getattr(result, "en_name", (result.NameEN or "") + " " + (result.LastNameEN or ""))
            self.religion = getattr(result, "religion", result.Religion)

            birth_raw = getattr(result, "birth_date", None) or getattr(result, "BirthdayTH", None)
            birth_date = self.thai_date_to_date(birth_raw) if birth_raw else None
            if birth_date:
                self.birthday = birth_date

            self.private_street = getattr(result, "private_street", (result.HouseNumber or "") + " " + (result.Road or ""))
            self.private_street2 = getattr(result, "private_street2", result.Subdistrict)
            self.private_city = getattr(result, "district", result.District)
            self.private_state_id = getattr(result, "province", result.Province)

            country = self.env.ref('base.th') 
            self.country_id = country
            self.private_country_id = country
        except Exception as e:
            raise UserError(f"อ่านข้อมูลจากภาพไม่สำเร็จ: {e}")
        finally:
            # ✅ ลบรูปทันทีหลังใช้งาน
            self.id_card_image = False