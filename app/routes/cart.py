from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from flask_login import login_required, current_user
from app import db
from app.models.users import Cart, CartItem
from app.models.productos import Producto

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('/')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.idUser).first()
    items = cart.items if cart else []
    total_general = sum(item.quantity * item.price for item in items)
    return render_template('cart.html', cart=cart, items=items, total_general=total_general)

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Producto.query.get(product_id)
    if not product:
        flash('Producto no encontrado.', 'danger')
        return redirect(url_for('main'))
    try:
        quantity = int(request.form.get('quantity', 1))
    except Exception:
        quantity = 1
    if quantity < 1:
        flash('Cantidad inválida.', 'danger')
        return redirect(url_for('cart.view_cart'))
    if product.stock < quantity:
        flash('No hay suficiente stock disponible.', 'danger')
        return redirect(url_for('cart.view_cart'))
    cart = Cart.query.filter_by(user_id=current_user.idUser).first()
    if not cart:
        cart = Cart(user_id=current_user.idUser)
        db.session.add(cart)
        db.session.commit()
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if item:
        if product.stock < item.quantity + quantity:
            flash('No hay suficiente stock disponible.', 'danger')
            return redirect(url_for('cart.view_cart'))
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, product_name=product.nombre, price=product.precio, quantity=quantity)
        db.session.add(item)
    db.session.commit()
    flash('Producto agregado al carrito.', 'success')
    return redirect(url_for('cart.view_cart'))

@bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Producto eliminado del carrito.', 'success')
    else:
        flash('Producto no encontrado en el carrito.', 'danger')
    return redirect(url_for('cart.view_cart'))

@bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    item = CartItem.query.get(item_id)
    if item and item.cart.user_id == current_user.idUser:
        try:
            new_quantity = int(request.form.get('quantity', 1))
            if new_quantity < 1:
                db.session.delete(item)
                flash('Producto eliminado del carrito.', 'success')
            else:
                item.quantity = new_quantity
                flash('Cantidad actualizada.', 'success')
            db.session.commit()
        except Exception:
            flash('Cantidad inválida.', 'danger')
    else:
        flash('Producto no encontrado en el carrito.', 'danger')
    return redirect(url_for('cart.view_cart'))
