from flask import Blueprint, redirect, url_for, render_template, flash, make_response, render_template_string, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.users import Cart, CartItem, Order, OrderItem
from app.models.payment_proof import PaymentProof
import pdfkit
from werkzeug.utils import secure_filename
import os

bp = Blueprint('orders', __name__, url_prefix='/orders')

@bp.route('/create', methods=['POST'])
@login_required
def create_order():
    cart = Cart.query.filter_by(user_id=current_user.idUser).first()
    if not cart or not cart.items:
        flash('El carrito está vacío.', 'danger')
        return redirect(url_for('cart.view_cart'))
    metodo_pago = request.form.get('metodo_pago')
    # Obtener dirección y coordenadas
    direccion_envio = request.form.get('direccion_envio')
    latitud_envio = request.form.get('latitud_envio')
    longitud_envio = request.form.get('longitud_envio')
    # Crear la orden primero
    order = Order(user_id=current_user.idUser, status='pendiente')
    order.direccion_envio = direccion_envio
    order.latitud_envio = latitud_envio
    order.longitud_envio = longitud_envio
    db.session.add(order)
    db.session.commit()
    for item in cart.items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, price=item.price)
        db.session.add(order_item)
    db.session.commit()

    # Procesar comprobante para Nequi y Efectivo
    file = request.files.get('comprobante_pago')
    payment_proof = None
    if metodo_pago in ['numero', 'efectivo']:
        if not file or file.filename == '':
            flash('Debes subir el comprobante de pago en PDF.', 'danger')
            db.session.delete(order)
            db.session.commit()
            return redirect(url_for('cart.view_cart'))
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            flash('Solo se permite subir comprobantes en formato PDF.', 'danger')
            db.session.delete(order)
            db.session.commit()
            return redirect(url_for('cart.view_cart'))
        # Nombre único: orderID_timestamp.pdf
        import time
        unique_filename = f"order_{order.id}_{int(time.time())}.pdf"
        upload_folder = os.path.join(current_app.root_path, 'static', 'comprobantes')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        try:
            file.save(filepath)
        except Exception as e:
            flash(f'Error al guardar el comprobante: {e}', 'danger')
            db.session.delete(order)
            db.session.commit()
            return redirect(url_for('cart.view_cart'))
        payment_proof = PaymentProof(order_id=order.id, filename=unique_filename, mimetype=file.mimetype)
        db.session.add(payment_proof)
        db.session.commit()
        order.payment_proof_id = payment_proof.id
        db.session.commit()

    # Eliminar el carrito
    db.session.delete(cart)
    db.session.commit()

    # Notificar al admin por correo (siempre, adjunta comprobante si existe)
    from flask_mail import Message
    from app.mail import mail
    from app.models.users import Users
    admin_user = Users.query.filter_by(role='admin').first()
    admin_email = admin_user.email if admin_user else 'cuentaintercambio606@gmail.com'
    msg = Message(
        subject=f'Nuevo pedido #{order.id} pendiente de aprobación',
        recipients=[admin_email],
        body=f'Se ha realizado un nuevo pedido #{order.id} por el usuario {current_user.nameUser} ({current_user.email}).\n\nRevisa el comprobante de pago adjunto para aceptar o rechazar el pedido.\nDirección de entrega: {order.direccion_envio or "No especificada"}',
    )
    # Adjuntar el archivo comprobante al correo solo si existe
    if payment_proof:
        try:
            with open(filepath, 'rb') as fp:
                msg.attach(payment_proof.filename, 'application/pdf', fp.read())
        except Exception as e:
            flash(f'No se pudo adjuntar el comprobante al correo: {e}', 'warning')
    try:
        mail.send(msg)
    except Exception as e:
        flash(f'No se pudo notificar al admin por correo: {e}', 'warning')

    if metodo_pago == 'efectivo':
        flash('Pedido realizado correctamente. Pagarás en efectivo al recibir el pedido.', 'success')
    elif metodo_pago == 'tarjeta':
        flash('Pago simulado con tarjeta realizado correctamente. Pedido registrado.', 'success')
    else:
        flash('Pedido realizado correctamente. El comprobante fue enviado para revisión.', 'success')
    return redirect(url_for('orders.view_orders'))

@bp.route('/')
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=current_user.idUser).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@bp.route('/accept/<int:order_id>', methods=['POST'])
@login_required
def accept_order(order_id):
    from app.models.users import Users
    from app.models.productos import Producto
    if current_user.role != 'admin':
        flash('Solo el administrador puede aceptar pedidos.', 'danger')
        return redirect(url_for('orders.view_orders'))
    order = Order.query.get(order_id)
    if order and order.status == 'pendiente':
        # Descontar stock de cada producto
        for item in order.items:
            producto = Producto.query.get(item.product_id)
            if producto:
                producto.stock = max(producto.stock - item.quantity, 0)
        order.status = 'aceptado'
        db.session.commit()
        # Enviar correo al cliente
        from app.models.users import Users
        from flask_mail import Message
        from app.mail import mail
        user = Users.query.get(order.user_id)
        if user and user.email:
            msg = Message('Tu pedido en construmax fue aceptado', recipients=[user.email])
            msg.body = f"Hola {user.nameUser},\n\nTu pedido #{order.id} ha sido aceptado y está en proceso. Pronto recibirás más información sobre el envío.\n\n¡Gracias por confiar en construmax!"
            try:
                mail.send(msg)
            except Exception as e:
                flash(f'No se pudo enviar el correo: {e}', 'warning')
        flash('Pedido aceptado, stock actualizado y correo enviado al cliente.', 'success')
    else:
        flash('Pedido no encontrado o ya aceptado.', 'danger')
    # Redirigir al panel de admin
    return redirect(url_for('auth.dashboard'))

@bp.route('/generate_invoice/<int:order_id>', methods=['POST'])
@login_required
def generate_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.idUser and current_user.role != 'admin':
        flash('No tienes permiso para ver esta factura.', 'danger')
        return redirect(url_for('orders.view_orders'))
    if order.status != 'aceptado':
        flash('La factura solo está disponible para pedidos aceptados.', 'danger')
        return redirect(url_for('orders.view_orders'))
    items = order.items
    total_general = sum(item.quantity * item.price for item in items)
    from app.models.users import Users
    user = Users.query.get(order.user_id)
    html = render_template('invoice.html', order=order, items=items, total_general=total_general, user=user)
    import pdfkit
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html, False, configuration=config)
    from flask import make_response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factura_{order.id}.pdf'
    return response

@bp.route('/detalle/<int:order_id>')
@login_required
def detalle_pedido(order_id):
    order = Order.query.get_or_404(order_id)
    user = db.session.query(Cart).get(order.user_id)
    from app.models.users import Users
    usuario = Users.query.get(order.user_id)
    return render_template_string('''
        <div><strong>Fecha:</strong> {{ order.created_at.strftime('%d/%m/%Y %H:%M') }}</div>
        <div><strong>Estado:</strong> {{ order.status }}</div>
        <div><strong>Email:</strong> {{ usuario.email if usuario else '' }}</div>
        <div><strong>Dirección de entrega:</strong> {{ order.direccion_envio or 'No especificada' }}</div>
        {% if order.latitud_envio and order.longitud_envio %}
        <div><a href="https://www.google.com/maps/search/?api=1&query={{ order.latitud_envio }},{{ order.longitud_envio }}" target="_blank">Ver en Google Maps</a></div>
        {% endif %}
        <div><strong>Productos:</strong>
            <ul>
            {% for item in order.items %}
                <li>{{ item.product_name }} x{{ item.quantity }} ({{ item.price }} c/u)</li>
            {% endfor %}
            </ul>
        </div>
        <div><strong>Comprobante:</strong>
            {% if order.payment_proof %}
                <a href="{{ url_for('static', filename='comprobantes/' ~ order.payment_proof.filename) }}" target="_blank">Ver comprobante</a>
            {% else %}
                No subido
            {% endif %}
        </div>
    ''', order=order, usuario=usuario)
