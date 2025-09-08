from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.users import Users
from app.models.productos import Producto

bp = Blueprint('auth', __name__)


# Cambiar la ruta de login a /login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    import random
    if request.method == 'POST':
        nameUser = request.form.get('nameUser')
        passwordUser = request.form.get('passwordUser')
        captcha = request.form.get('captcha')
        captcha_answer = session.get('captcha_answer')

        # Validar captcha
        if not captcha_answer or captcha != str(captcha_answer):
            flash('Captcha incorrecto. Por favor responde correctamente la pregunta.', 'danger')
            return render_template("login.html", captcha_question=session.get('captcha_question'))

        # Validar campos obligatorios
        if not all([nameUser, passwordUser]):
            flash('Usuario y contraseña son obligatorios.', 'danger')
            return render_template("login.html", captcha_question=session.get('captcha_question'))

        user = Users.query.filter_by(nameUser=nameUser).first()
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user.passwordUser, passwordUser):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('auth.dashboard'))
        flash('Credenciales inválidas. Por favor verifica tus datos.', 'danger')
        # Generar nueva captcha tras intento fallido
        a, b = random.randint(1, 9), random.randint(1, 9)
        session['captcha_question'] = f"¿Eres humano? Escribe el resultado: {a} + {b} ="
        session['captcha_answer'] = a + b
        return render_template("login.html", captcha_question=session['captcha_question'])
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    # Generar captcha al cargar la página
    a, b = random.randint(1, 9), random.randint(1, 9)
    session['captcha_question'] = f"¿Eres humano? Escribe el resultado: {a} + {b} ="
    session['captcha_answer'] = a + b
    return render_template("login.html", captcha_question=session['captcha_question'])

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
