FROM odoo:18

USER root

# 🔥 system deps
RUN apt-get update && apt-get install -y \
    python3-venv \
    python3-dev \
    build-essential \
    cmake \
    g++ \
    gcc \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# ✅ สำคัญ: ให้ venv เห็น Odoo
RUN python3 -m venv /opt/venv --system-site-packages

# ใช้ venv
ENV PATH="/opt/venv/bin:$PATH"

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# ⚡ ลดขนาด: ใช้ CPU torch
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# install python packages
RUN pip install --no-cache-dir \
    typhoon-ocr \
    easyocr \
    pillow \
    numpy \
    psycopg2-binary \
    face_recognition

USER odoo

# ✅ บังคับ Odoo ใช้ venv
CMD ["/opt/venv/bin/python", "/usr/bin/odoo", "-c", "/etc/odoo/odoo.conf"]