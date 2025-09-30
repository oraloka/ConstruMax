from flask import Blueprint, redirect, url_for, render_template, flash, make_response, render_template_string, request
from flask_login import login_required, current_user
from app import db
from app.models.users import Cart, CartItem, Order, OrderItem
import pdfkit

bp = Blueprint('orders', __name__, url_prefix='/orders')

@bp.route('/create', methods=['POST'])
@login_required
def create_order():
    cart = Cart.query.filter_by(user_id=current_user.idUser).first()
    if not cart or not cart.items:
        flash('El carrito está vacío.', 'danger')
        return redirect(url_for('cart.view_cart'))
    order = Order(user_id=current_user.idUser, status='pendiente')
    db.session.add(order)
    db.session.commit()
    for item in cart.items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, price=item.price)
        db.session.add(order_item)
    db.session.delete(cart)
    db.session.commit()
    flash('Pedido realizado correctamente.', 'success')
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
