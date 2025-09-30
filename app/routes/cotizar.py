from flask import Blueprint, render_template, request, session, redirect, url_for, send_file, flash
from io import BytesIO
from flask_mail import Message
from app import db
import pdfkit
from flask_mail import Message
from flask import current_app as app

bp = Blueprint('cotizar', __name__, url_prefix='/cotizar')

def calcular_descuento(total):
    if total >= 5000000:
        descuento = int(total * 0.07)  # 7% de descuento
        return descuento
    return 0

@bp.route('/', methods=['GET', 'POST'])
def cotizar():
    from app.models.productos import Producto
    productos = Producto.query.filter(Producto.stock > 0).all()
    cotizacion = None
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        productos_seleccionados = []
        total_estimado = 0
        for producto in productos:
            cantidad = int(request.form.get(f'cantidad_{producto.id}', 0))
            if cantidad > 0:
                subtotal = cantidad * producto.precio
                productos_seleccionados.append({
                    'nombre': producto.nombre,
                    'cantidad': cantidad,
                    'precio': producto.precio,
                    'subtotal': subtotal
                })
                total_estimado += subtotal
        descuento = calcular_descuento(total_estimado)
        total_final = total_estimado - descuento
        cotizacion = {
            'nombre': nombre,
            'correo': correo,
            'productos': productos_seleccionados,
            'total_estimado': total_estimado,
            'descuento': descuento,
            'total_final': total_final
        }
        session['cotizacion'] = cotizacion
    return render_template('cotizar.html', cotizacion=session.get('cotizacion'), productos=productos)

@bp.route('/descargar_pdf')
def descargar_pdf():
    cotizacion = session.get('cotizacion')
    if not cotizacion:
        flash('No hay cotización para descargar.', 'danger')
        return redirect(url_for('cotizar.cotizar'))
    html = render_template('cotizar_pdf.html', cotizacion=cotizacion)
    config = pdfkit.configuration(wkhtmltopdf=r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html, False, configuration=config)
    return send_file(BytesIO(pdf), download_name='cotizacion.pdf', as_attachment=True)

@bp.route('/enviar_email')
def enviar_email():
    cotizacion = session.get('cotizacion')
    if not cotizacion:
        flash('No hay cotización para enviar.', 'danger')
        return redirect(url_for('cotizar.cotizar'))
    html = render_template('cotizar_pdf.html', cotizacion=cotizacion)
    config = pdfkit.configuration(wkhtmltopdf=r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html, False, configuration=config)
    msg = Message('Tu cotización ConstruMax', recipients=[cotizacion['correo']])
    msg.body = 'Adjunto encontrarás tu cotización profesional de ConstruMax.'
    msg.attach('cotizacion.pdf', 'application/pdf', pdf)
    mail = app.extensions.get('mail')
    mail.send(msg)
    flash('Cotización enviada exitosamente al correo.', 'success')
    return redirect(url_for('cotizar.cotizar'))
