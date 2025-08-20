from flask import Blueprint, render_template, request, redirect, url_for
from app.models.productos import Producto
from app import db

bp = Blueprint('productos', __name__)

# Vista general de productos
@bp.route('/productos')
def productos():
    productos = Producto.query.all()
    return render_template('productos/productos.html', productos=productos)

# Vista por categoría
@bp.route('/productos/<categoria>')
def productos_categoria(categoria):
    productos = Producto.query.filter_by(categoria=categoria).all()
    return render_template(f'productos/{categoria}.html', productos=productos)

# Vista para agregar productos (solo ejemplo, puedes protegerla para admin)
@bp.route('/productos/agregar', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        precio = float(request.form['precio'])
        imagen = request.form.get('imagen', '')
        nuevo = Producto(nombre=nombre, descripcion=descripcion, categoria=categoria, precio=precio, imagen=imagen)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('productos.productos'))
    return render_template('productos/agregar.html')
