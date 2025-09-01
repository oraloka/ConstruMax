from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.users import Users
from app.models.productos import Producto

bp = Blueprint('auth', __name__)


# Cambiar la ruta de login a /login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nameUser = request.form['nameUser']
        passwordUser = request.form['passwordUser']
        user = Users.query.filter_by(nameUser=nameUser).first()
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user.passwordUser, passwordUser):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('auth.dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return render_template("login.html")

@bp.route('/dashboard')
@login_required
def dashboard():    
    if current_user.role == 'admin':
        usuarios = Users.query.all()
        productos = Producto.query.all()
        from app.models.users import Order
        pedidos = Order.query.order_by(Order.created_at.desc()).all()
        return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos, pedidos=pedidos)
    elif current_user.bloqueado:
        flash('Tu usuario está bloqueado. Contacta al administrador.', 'danger')
        logout_user()
        return redirect(url_for('auth.login'))
    else:
        # Obtener categorías únicas
        categorias = Producto.query.with_entities(Producto.categoria).distinct().all()
        categorias = [c[0] for c in categorias if c[0]]
        productos = Producto.query.all()
        return render_template('user_dashboard.html', categorias=categorias, productos=productos)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
