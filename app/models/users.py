from flask_login import UserMixin
from app import db
from app.models.payment_proof import PaymentProof


class Users(db.Model, UserMixin):
    __tablename__ = 'user'
    idUser = db.Column(db.Integer, primary_key=True)
    nameUser = db.Column(db.String(80), unique=True, nullable=False)
    apellidoUser = db.Column(db.String(80), nullable=False)
    telefonoUser = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    direccionUser = db.Column(db.String(255), nullable=False)
    passwordUser = db.Column(db.String(120), nullable=False)
    foto_perfil = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default='user')
    bloqueado = db.Column(db.Boolean, default=False)

    def get_id(self):
        return str(self.idUser)
    

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.idUser'))
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=db.func.now())

class CartItem(db.Model):
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.idUser'))
    created_at = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(20), default='pendiente')  # aceptado, en_camino, entregado
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment_proof_id = db.Column(db.Integer, db.ForeignKey('payment_proof.id'))  # Relación con comprobante de pago
    direccion_envio = db.Column(db.String(255))
    latitud_envio = db.Column(db.String(64))
    longitud_envio = db.Column(db.String(64))

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)