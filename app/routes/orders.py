from flask import Blueprint, redirect, url_for, render_template, flash, make_response, render_template_string, request
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
    if metodo_pago == 'efectivo':
        order = Order(user_id=current_user.idUser, status='pendiente')
        order.direccion_envio = direccion_envio
        order.latitud_envio = latitud_envio
        order.longitud_envio = longitud_envio
        db.session.add(order)
        db.session.commit()
        for item in cart.items:
            order_item = OrderItem(order_id=order.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, price=item.price)
            db.session.add(order_item)
        db.session.delete(cart)
        db.session.commit()
        flash('Pedido realizado correctamente. Pagarás en efectivo al recibir el pedido.', 'success')
        return redirect(url_for('orders.view_orders'))
    elif metodo_pago == 'tarjeta':
        # Simulación de pago con tarjeta
        nombre_tarjeta = request.form.get('nombre_tarjeta')
        numero_tarjeta = request.form.get('numero_tarjeta')
        expiracion_tarjeta = request.form.get('expiracion_tarjeta')
        cvv_tarjeta = request.form.get('cvv_tarjeta')
        # No se almacena nada, solo simula
        order = Order(user_id=current_user.idUser, status='pendiente')
        order.direccion_envio = direccion_envio
        order.latitud_envio = latitud_envio
        order.longitud_envio = longitud_envio
        db.session.add(order)
        db.session.commit()
        for item in cart.items:
            order_item = OrderItem(order_id=order.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, price=item.price)
            db.session.add(order_item)
        db.session.delete(cart)
        db.session.commit()
        flash('Pago simulado con tarjeta realizado correctamente. Pedido registrado.', 'success')
        return redirect(url_for('orders.view_orders'))
    # Procesar comprobante de pago
    file = request.files.get('comprobante_pago')
    if not file or file.filename == '':
        flash('Debes subir el comprobante de pago.', 'danger')
        return redirect(url_for('cart.view_cart'))
    filename = secure_filename(file.filename)
    upload_folder = os.path.join('static', 'comprobantes')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    order = Order(user_id=current_user.idUser, status='pendiente')
    order.direccion_envio = direccion_envio
    order.latitud_envio = latitud_envio
    order.longitud_envio = longitud_envio
    db.session.add(order)
    db.session.commit()
    for item in cart.items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, price=item.price)
        db.session.add(order_item)
    # Guardar comprobante en la base de datos
    payment_proof = PaymentProof(order_id=order.id, filename=filename, mimetype=file.mimetype)
    db.session.add(payment_proof)
    db.session.delete(cart)
    db.session.commit()

    # Notificar al admin por correo (asegura que el correo se envía en todos los métodos)
    from flask_mail import Message
    from app.mail import mail
    from app.models.users import Users
    # Buscar el primer usuario admin en la base de datos
    admin_user = Users.query.filter_by(role='admin').first()
    admin_email = admin_user.email if admin_user else 'cuentaintercambio606@gmail.com'
    msg = Message(
        subject=f'Nuevo pedido #{order.id} pendiente de aprobación',
        recipients=[admin_email],
        body=f'Se ha realizado un nuevo pedido #{order.id} por el usuario {current_user.nameUser} ({current_user.email}).\n\nRevisa el comprobante de pago o la evidencia adjunta para aceptar o rechazar el pedido.\nDirección de entrega: {order.direccion_envio or "No especificada"}',
    )
    if metodo_pago == 'numero' and file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = os.path.join('static', 'comprobantes')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        payment_proof = PaymentProof(order_id=order.id, filename=filename, mimetype=file.mimetype)
        db.session.add(payment_proof)
        db.session.commit()
        with open(filepath, 'rb') as fp:
            msg.attach(filename, file.mimetype, fp.read())
    elif metodo_pago == 'efectivo' and file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = os.path.join('static', 'comprobantes')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        payment_proof = PaymentProof(order_id=order.id, filename=filename, mimetype=file.mimetype)
        db.session.add(payment_proof)
        db.session.commit()
        with open(filepath, 'rb') as fp:
            msg.attach(filename, file.mimetype, fp.read())
    try:
        mail.send(msg)
    except Exception as e:
        flash(f'No se pudo notificar al admin por correo: {e}', 'warning')

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
            msg = Message('Tu pedido en ConstruMax fue aceptado', recipients=[user.email])
            msg.body = f"Hola {user.nameUser},\n\nTu pedido #{order.id} ha sido aceptado y está en proceso. Pronto recibirás más información sobre el envío.\n\n¡Gracias por confiar en ConstruMax!"
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
        <div><strong>ID Pedido:</strong> {{ order.id }}</div>
        <div><strong>Fecha:</strong> {{ order.created_at.strftime('%d/%m/%Y %H:%M') }}</div>
        <div><strong>Estado:</strong> {{ order.status }}</div>
        <div><strong>Usuario:</strong> {{ usuario.nameUser if usuario else order.user_id }} (ID: {{ order.user_id }})</div>
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
                <a href="{{ url_for('static', filename='comprobantes/' ~ order.payment_proof.filename) }}" target="_blank">Ver imagen</a>
            {% else %}
                No subido
            {% endif %}
        </div>
    ''', order=order, usuario=usuario)
