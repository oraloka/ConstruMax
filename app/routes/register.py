from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models.users import Users
from werkzeug.security import generate_password_hash

bp = Blueprint('register', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nameUser = request.form['nameUser']
        apellidoUser = request.form['apellidoUser']
        telefonoUser = request.form['telefonoUser']
        email = request.form['email']
        direccionUser = request.form['direccionUser']
        passwordUser = request.form['passwordUser']

        if Users.query.filter_by(nameUser=nameUser).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('register.register'))
        if Users.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'danger')
            return redirect(url_for('register.register'))

        import re
        # Validación de contraseña fuerte
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$'
        if not re.match(password_regex, passwordUser):
            flash('La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un símbolo.', 'danger')
            return redirect(url_for('register.register'))

        hashed_password = generate_password_hash(passwordUser)
        new_user = Users(
            nameUser=nameUser,
            apellidoUser=apellidoUser,
            telefonoUser=telefonoUser,
            email=email,
            direccionUser=direccionUser,
            passwordUser=hashed_password,
            role='user'  # Forzar rol user
        )
        db.session.add(new_user)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')
