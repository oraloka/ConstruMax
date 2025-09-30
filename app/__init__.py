from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config.from_object('config.Config')

    # Configuración de Flask-Mail (debe ir después de crear 'app')
    from app.mail import mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'cuentaintercambio606@gmail.com'  # Cambia esto por tu correo real
    app.config['MAIL_PASSWORD'] = 'lryy kysq zxkh hzsq'        # Cambia esto por tu contraseña real o usa variable de entorno
    app.config['MAIL_DEFAULT_SENDER'] = 'cuentaintercambio606@gmail.com'
    mail.init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(idUser):
        from .models.users import Users
        return Users.query.get(int(idUser))

    from app.routes import auth
    from app.routes import register
    from app.routes import users_route
    from app.routes import cart
    from app.routes import orders
    from app.routes import cotizar
    from app.routes import reset_password
    app.register_blueprint(auth.bp)
    app.register_blueprint(register.bp)
    app.register_blueprint(users_route.bp)
    app.register_blueprint(cart.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(cotizar.bp)
    app.register_blueprint(reset_password.bp)

    # Ruta principal para la vista principal
    # Filtro para mostrar precios en formato COP
    from markupsafe import Markup
    def cop_format(value):
        try:
            value = float(value)
            return Markup(f'$ {value:,.0f}'.replace(',', '.'))
        except Exception:
            return value

    # Filtro para separar miles con coma
    def comma_format(value):
        try:
            return f"{int(value):,}".replace(",", ".")
        except Exception:
            return value
    app.jinja_env.filters['comma'] = comma_format
    app.jinja_env.filters['cop'] = cop_format

    @app.route('/')
    def main():
        from .models.productos import Producto
        productos = Producto.query.filter_by(destacado=True).all()
        return render_template('main.html', productos=productos)

    # Crear tablas y usuario admin automáticamente si no existen
    from app.models.users import Users
    from werkzeug.security import generate_password_hash
    with app.app_context():
        db.create_all()
        admin_email = 'cajlpj@gmail.com'
        admin_password = 'CRclass123@'
        admin = Users.query.filter_by(email=admin_email).first()
        if not admin:
            hashed_password = generate_password_hash(admin_password)
            admin_user = Users(
                nameUser='Admin',
                apellidoUser='Principal',
                telefonoUser='0000000000',
                email=admin_email,
                direccionUser='Oficina Principal',
                passwordUser=hashed_password,
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
    return app