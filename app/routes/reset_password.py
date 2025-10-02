from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import Users
from app import db
from werkzeug.security import generate_password_hash
from flask_mail import Message
from app.mail import mail
import secrets

bp = Blueprint('reset_password', __name__, url_prefix='/reset_password')

# Almacén temporal de tokens (en producción usar base de datos o Redis)
token_store = {}

@bp.route('/', methods=['GET', 'POST'])
def request_reset():
    if request.method == 'POST':
        email = request.form['email']
        user = Users.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            token_store[token] = user.idUser
            reset_link = url_for('reset_password.reset_with_token', token=token, _external=True)
            msg = Message('Recupera tu contraseña - construmax', recipients=[email])
            msg.body = f"Hola,\n\nPara restablecer tu contraseña haz clic en el siguiente enlace:\n{reset_link}\n\nSi no solicitaste este cambio, ignora este correo."
            try:
                mail.send(msg)
                flash('Se ha enviado un enlace de recuperación a tu correo.', 'success')
            except Exception as e:
                flash(f'No se pudo enviar el correo: {e}', 'danger')
        else:
            flash('No existe una cuenta con ese correo.', 'danger')
    return render_template('request_reset.html')

@bp.route('/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    user_id = token_store.get(token)
    if not user_id:
        flash('El enlace no es válido o ha expirado.', 'danger')
        return redirect(url_for('reset_password.request_reset'))
    if request.method == 'POST':
        password = request.form['password']
        user = Users.query.get(user_id)
        if user:
            user.passwordUser = generate_password_hash(password)
            db.session.commit()
            del token_store[token]
            flash('Contraseña actualizada correctamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('reset_password.html', token=token)
