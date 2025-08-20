from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models.users import Users
from werkzeug.security import generate_password_hash

bp = Blueprint('register', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nameUser = request.form['nameUser']
        passwordUser = request.form['passwordUser']
        
        if Users.query.filter_by(nameUser=nameUser).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register.register'))

        role = request.form.get('role', 'user')
        hashed_password = generate_password_hash(passwordUser)
        new_user = Users(nameUser=nameUser, passwordUser=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')
