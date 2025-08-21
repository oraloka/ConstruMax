from app import db

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255))
    presentacion = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    destacado = db.Column(db.Boolean, default=False)
    # Puedes agregar más campos según lo que maneje la tienda

    def __repr__(self):
        return f'<Producto {self.nombre}>'
