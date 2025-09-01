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
    order = Order(user_id=current_user.idUser, status='aceptado')
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
