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
    app.register_blueprint(auth.bp)
    app.register_blueprint(register.bp)
    app.register_blueprint(users_route.bp)
    app.register_blueprint(cart.bp)
    app.register_blueprint(orders.bp)

    # Ruta principal para la vista principal
    # Filtro para mostrar precios en formato COP
    from markupsafe import Markup
    def cop_format(value):
        try:
            value = float(value)
            return Markup(f'$ {value:,.0f}'.replace(',', '.'))
        except Exception:
            return value
    app.jinja_env.filters['cop'] = cop_format

    @app.route('/')
    def main():
        from .models.productos import Producto
        productos = Producto.query.filter_by(destacado=True).all()
        return render_template('main.html', productos=productos)

    return app