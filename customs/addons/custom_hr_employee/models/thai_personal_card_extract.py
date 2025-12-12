import datetime
import base64
import tempfile
import unicodedata
from io import BytesIO
from odoo import models, fields, api
from odoo.exceptions import UserError
from cryptography.fernet import Fernet
from PIL import Image
from typhoon_ocr import ocr_document
import re

class HrPersonalCardExtract(models.Model):
    _inherit = 'hr.employee'

    id_card_image = fields.Binary(string='ID Card Image')
    id_card_image_filename = fields.Char(string="ID Card Filename")

    religion = fields.Char(string="Religion")
    identification_id_encrypted = fields.Char(store=True)
    birthday = fields.Date(string="Date of Birth")

    identification_id = fields.Char(
        string="ID Number",
        compute="_compute_identification_id",
        inverse="_inverse_identification_id",
        store=False,
    )

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

    def extract_info_from_image(self):
        for rec in self:
            rec._extract_from_image_single()

    @staticmethod
    def thai_date_to_date(date_str):
        thai_months = {
            'ม.ค': '01', 'ก.พ': '02', 'มี.ค': '03', 'เม.ย': '04',
            'พ.ค': '05', 'มิ.ย': '06', 'ก.ค': '07', 'ส.ค': '08',
            'ก.ย': '09', 'ต.ค': '10', 'พ.ย': '11', 'ธ.ค': '12'
        }

        try:
            date_str = unicodedata.normalize("NFKC", date_str).replace('\u00a0', ' ').strip()
            parts = date_str.split()
            if len(parts) != 3:
                return None

            day = parts[0]
            raw_month = parts[1].replace(".", "")
            year = int(parts[2]) - 543

            month = next((v for k, v in thai_months.items() if raw_month in k.replace(".", "")), None)
            if not month:
                return None

            return datetime.datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
        except:
            return None

    @staticmethod   
    def scan_id_card(image_path):
        text_md = ocr_document(
            image_path,  base_url="http://localhost:11434/v1",
            model="scb10x/typhoon-ocr-3b",
            page_num=1
        )
        text = text_md.replace("\n", " ").replace("#", "").strip()

        thai_fullname = None
        match = re.search(r"ชื่อตัวและชื่อสกุล[:\-]?\s*(.+?)(?=\s{2,}|วันเกิด|เกิดวันที่|วันออกบัตร|$)", text)
        if match:
            thai_fullname = match.group(1).strip()

        thai_name_pattern = r"(นางสาว|นาง|นาย)\s[ก-๙]+\s[ก-๙]+(?:\s[ก-๙]+)?"
        thai_names = re.findall(thai_name_pattern, text)

        return {
            "raw_text": text,
            "thai_fullname": thai_fullname,
            "thai_names": thai_names,
        }

    def _extract_from_image_single(self):
        if not self.id_card_image:
            raise UserError("กรุณาอัปโหลดรูปบัตรประชาชนก่อน")

        image_data = base64.b64decode(self.id_card_image)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            with Image.open(BytesIO(image_data)) as img:
                img = img.convert("RGB")
                img.thumbnail((1000, 1000))
                img.save(f, format="JPEG")
            temp_path = f.name

        try:
            result = self.scan_id_card(temp_path)

            text = result.get("raw_text", "")
            thai_names = result.get("thai_fullname")

            print("text = ", text)         
            print("thai_names = ", thai_names)

            # ล้างข้อความให้เหลือเฉพาะตัวเลข
            digits_only = re.sub(r"[^0-9]", "", text)

            # หาเลขประจำตัวประชาชน 13 หลัก
            id_match = re.search(r"\d{13}", digits_only)
            if not id_match:
                raise UserError("ไม่พบเลขประจำตัวประชาชนในภาพ")

            id_number = id_match.group(0)
            self.identification_id_encrypted = self._get_or_create_fernet().encrypt(id_number.encode()).decode()

            self.name = thai_names.strip().rstrip("-").strip()

            # จับที่อยู่ด้วยหลายรูปแบบ
            address = ''
            address_patterns = [
                r"ที่อยู่\s*[-:]\s*(.+?)\s+(วันออกบัตร|Date of Issue|$)",
                r"Address\s*[-:]\s*(.+?)\s+(Date of Issue|$)",
                r"(\d{1,4}\s+หมู่ที่\s*\d{1,2}.*?(อ\.|อำเภอ).*?(จ\.|จังหวัด).*?)(\s{2,}|-|$)",
            ]

            for pattern in address_patterns:
                address_match = re.search(pattern, text, flags=re.DOTALL)
                if address_match:
                    address = address_match.group(1).strip()
                    break

            self.private_street = address

            # เพิ่มส่วนหา วันเกิด
            birth_date = None
            birth_match = re.search(r"(?:เกิดวันที่|Date of Birth)\s*[:-]?\s*([0-9]{1,2}\s*[ก-๙\.]+\s*[0-9]{4})", text)
            if birth_match:
                birth_str = birth_match.group(1).strip()
                birth_date = self.thai_date_to_date(birth_str)

            self.birthday = birth_date

            # แก้ regex ศาสนาให้ใช้ตรงๆ โดยไม่ต้อง mapping แล้ว
            religion_match = re.search(r"\b(พุทธ|อิสลาม|คริสต์|พราหมณ์|ซิกข์|อื่น\s*ๆ|ไม่ระบุ)\b", text)
            if religion_match:
                self.religion = religion_match.group(1)

            # ตั้งค่า country_id สำหรับข้อมูลส่วนตัว
            country = self.env.ref('base.th')
            self.country_id = country
            self.private_country_id = country

        except Exception as e:
            raise UserError(f"อ่านข้อมูลจากภาพไม่สำเร็จ: {e}")
