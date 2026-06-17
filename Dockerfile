FROM odoo:17.0

USER root
RUN pip3 install --no-cache-dir openpyxl==3.1.5 qrcode[pil]==7.4.2
USER odoo
