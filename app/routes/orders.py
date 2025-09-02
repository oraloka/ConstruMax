from flask import Blueprint, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from app import db
from app.models.users import Cart, CartItem, Order, OrderItem

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
        flash('Pedido aceptado y stock actualizado.', 'success')
    else:
        flash('Pedido no encontrado o ya aceptado.', 'danger')
    # Redirigir al panel de admin
    return redirect(url_for('auth.dashboard'))
