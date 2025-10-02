INSTRUCCIONES PARA PDF AUTOMÁTICO EN WINDOWS

1. Instala las dependencias de Python normalmente:
   pip install -r requirements.txt

2. Descarga el instalador de wkhtmltopdf para Windows desde:
   https://wkhtmltopdf.org/downloads.html

3. Instala wkhtmltopdf y asegúrate de que el ejecutable esté en:
   C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe

4. Si usas otra ruta, actualiza la línea de configuración en tu código:
   pdfkit.configuration(wkhtmltopdf=r'RUTA_A_TU_WKHTMLTOPDF.EXE')

5. ¡Listo! Ahora solo sube los cambios y tu entorno generará PDFs correctamente.