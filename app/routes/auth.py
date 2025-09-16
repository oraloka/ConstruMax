from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.models.users import Users
from app.models.productos import Producto
bp = Blueprint('auth', __name__)

import os
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename


# Vista de perfil para usuario
@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    if user.role == 'admin':
        return redirect(url_for('auth.admin_profile'))
    if request.method == 'POST':
        user.nameUser = request.form.get('nameUser', user.nameUser)
        user.apellidoUser = request.form.get('apellidoUser', user.apellidoUser)
        user.telefonoUser = request.form.get('telefonoUser', user.telefonoUser)
        user.email = request.form.get('email', user.email)
        user.direccionUser = request.form.get('direccionUser', user.direccionUser)
        foto = request.files.get('foto_perfil')
        if foto and foto.filename:
            filename = secure_filename(foto.filename)
            ruta = os.path.join('app/static/img', filename)
            foto.save(ruta)
            user.foto_perfil = url_for('static', filename=f'img/{filename}')
        password = request.form.get('passwordUser')
        password_confirm = request.form.get('passwordUserConfirm')
        if password:
            if password == password_confirm:
                user.passwordUser = generate_password_hash(password)
                flash('Contraseña actualizada correctamente.', 'success')
            else:
                flash('Las contraseñas no coinciden.', 'danger')
                return render_template('perfil.html')
        from app import db
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('perfil.html')

# Vista de perfil para admin
@bp.route('/admin_profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    user = current_user
    if user.role != 'admin':
        return redirect(url_for('auth.profile'))
    if request.method == 'POST':
        user.nameUser = request.form.get('nameUser', user.nameUser)
        user.apellidoUser = request.form.get('apellidoUser', user.apellidoUser)
        user.telefonoUser = request.form.get('telefonoUser', user.telefonoUser)
        user.email = request.form.get('email', user.email)
        user.direccionUser = request.form.get('direccionUser', user.direccionUser)
        foto = request.files.get('foto_perfil')
        if foto and foto.filename:
            filename = secure_filename(foto.filename)
            ruta = os.path.join('app/static/img', filename)
            foto.save(ruta)
            user.foto_perfil = url_for('static', filename=f'img/{filename}')
        password = request.form.get('passwordUser')
        password_confirm = request.form.get('passwordUserConfirm')
        if password:
            if password == password_confirm:
                user.passwordUser = generate_password_hash(password)
                flash('Contraseña actualizada correctamente.', 'success')
            else:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('auth.admin_profile'))
        from app import db
        db.session.commit()
        flash('Perfil de administrador actualizado correctamente.', 'success')
        return redirect(url_for('auth.admin_profile'))
    # Renderizar la sección de admin en el dashboard
    usuarios = Users.query.all()
    productos = Producto.query.all()
    categorias = Producto.query.with_entities(Producto.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    from app.models.users import Order
    pedidos = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos, pedidos=pedidos, categorias=categorias, admin_info=True)


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
        categorias = Producto.query.with_entities(Producto.categoria).distinct().all()
        categorias = [c[0] for c in categorias if c[0]]
        from app.models.users import Order
        pedidos = Order.query.order_by(Order.created_at.desc()).all()
        return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos, pedidos=pedidos, categorias=categorias)
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
