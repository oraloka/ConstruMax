
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.productos import Producto
from app.models.users import Users
from app import db
import os
from werkzeug.utils import secure_filename

bp = Blueprint('productos', __name__)

@bp.route('/productos/destacados', methods=['POST'])
def destacados():
    ids_destacados = request.form.getlist('destacados')
    # Primero, desmarcar todos los productos
    Producto.query.update({Producto.destacado: False})
    db.session.commit()
    # Marcar los seleccionados como destacados
    for id_str in ids_destacados:
        producto = Producto.query.get(int(id_str))
        if producto:
            producto.destacado = True
    db.session.commit()
    flash('Productos destacados actualizados.', 'success')
    usuarios = Users.query.all()
    productos = Producto.query.all()
    return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos)

# Vista general de productos
@bp.route('/productos')
def productos():
    productos = Producto.query.all()
    return render_template('productos/productos.html', productos=productos)

# Vista por categoría
@bp.route('/productos/<categoria>')
def productos_categoria(categoria):
    productos = Producto.query.filter_by(categoria=categoria).all()
    return render_template(f'{categoria}.html', productos=productos)

# Vista para agregar productos (solo ejemplo, puedes protegerla para admin)
@bp.route('/productos/agregar', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        precio = float(request.form['precio'])
        presentacion = request.form.get('presentacion', '')
        marca = request.form.get('marca', '')
        imagen_file = request.files.get('imagen')
        imagen = ''
        if imagen_file and imagen_file.filename:
            filename = secure_filename(imagen_file.filename)
            ruta = os.path.join('app/static/img', filename)
            imagen_file.save(ruta)
            imagen = url_for('static', filename=f'img/{filename}')
        nuevo = Producto(nombre=nombre, descripcion=descripcion, categoria=categoria, precio=precio, imagen=imagen, presentacion=presentacion, marca=marca)
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto agregado correctamente.', 'success')
        return redirect(url_for('auth.dashboard'))
    # Obtener categorías únicas para el select
    categorias = db.session.query(Producto.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    return render_template('productos/agregar.html', categorias=categorias)

@bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.categoria = request.form['categoria']
        producto.precio = float(request.form['precio'])
        producto.presentacion = request.form.get('presentacion', '')
        producto.marca = request.form.get('marca', '')
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename:
            filename = secure_filename(imagen_file.filename)
            ruta = os.path.join('app/static/img', filename)
            imagen_file.save(ruta)
            producto.imagen = url_for('static', filename=f'img/{filename}')
        db.session.commit()
        flash('Producto editado correctamente.', 'success')
        return redirect(url_for('auth.dashboard'))
    return render_template('productos/editar.html', producto=producto)

@bp.route('/productos/eliminar/<int:id>')
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('auth.dashboard'))



@bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    usuario = Users.query.get_or_404(id)
    if request.method == 'POST':
        usuario.nameUser = request.form['nameUser']
        usuario.role = request.form['role']
        usuario.bloqueado = bool(request.form.get('bloqueado'))
        db.session.commit()
        flash('Usuario editado correctamente.', 'success')
        return redirect(url_for('auth.dashboard'))
    return render_template('usuarios/editar.html', usuario=usuario)

@bp.route('/usuarios/eliminar/<int:id>')
def eliminar_usuario(id):
    usuario = Users.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('auth.dashboard'))

@bp.route('/usuarios/bloquear/<int:id>')
def bloquear_usuario(id):
    usuario = Users.query.get_or_404(id)
    usuario.bloqueado = True
    db.session.commit()
    from app.models.productos import Producto
    usuarios = Users.query.all()
    productos = Producto.query.all()
    mensaje_bloqueo = 'Usuario bloqueado.'
    return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos, mensaje_bloqueo=mensaje_bloqueo)

@bp.route('/usuarios/desbloquear/<int:id>')
def desbloquear_usuario(id):
    usuario = Users.query.get_or_404(id)
    usuario.bloqueado = False
    db.session.commit()
    from app.models.productos import Producto
    usuarios = Users.query.all()
    productos = Producto.query.all()
    mensaje_desbloqueo = 'Usuario desbloqueado.'
    return render_template('admin_dashboard.html', usuarios=usuarios, productos=productos, mensaje_desbloqueo=mensaje_desbloqueo)
