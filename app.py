from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = '1' 

# Conexión a MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='A123456789!',
        database='minimercado'
    )
    return connection

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verduras')
def verduras():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM producto WHERE tipo = 'verdura'")
    verduras = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('verduras.html', productos=verduras)

@app.route('/frutas')
def frutas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM producto WHERE tipo = 'fruta'")
    frutas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('frutas.html', productos=frutas)

@app.route('/producto/<nombre>')
def producto(nombre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM producto WHERE nombre = %s", (nombre,))
    producto = cursor.fetchone()


    while cursor.nextset():
        pass

    cursor.close()
    conn.close()

    if not producto:
        return "Producto no encontrado", 404

    return render_template('producto.html', producto=producto)


@app.route('/recetas')
def recetas():
    return render_template('recetas.html')

@app.route('/quienessomos')
def quienessomos():
    return render_template('quienessomos.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cliente WHERE email = %s AND password = %s", (email, password))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            session['usuario'] = usuario['nombre']
            session['email'] = usuario['email']
            session['telefono'] = usuario['telefono']
            session['direccion'] = usuario['direccion']
            flash(f"Bienvenido, {usuario['nombre']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Credenciales incorrectas", "danger")

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO cliente (nombre, apellido, email, telefono, direccion, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, apellido, email, telefono, direccion, password))
            conn.commit()
            flash("Usuario registrado con éxito", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            flash(f"Error al registrar: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('registro.html')

@app.route('/carrito')
def carrito():
    carrito = session.get('carrito', {})
    productos = []
    total = 0

    for producto_id, item in carrito.items():
        subtotal = item['precio'] * item['cantidad']
        total += subtotal
        productos.append({
            'id': int(producto_id),
            'nombre': item['nombre'],
            'precio': item['precio'],
            'imagen': item['imagen'],
            'cantidad': item['cantidad'],
            'subtotal': subtotal
        })


    return render_template('carrito.html', productos=productos, total=total)

@app.route('/agregar_carrito/<int:id>', methods=['POST'])
def agregar_carrito(id):
    cantidad = int(request.form.get('cantidad', 1))

    if 'carrito' not in session:
        session['carrito'] = {}

    carrito = session['carrito']

    if cantidad == 0:
        carrito.pop(str(id), None)
        session['carrito'] = carrito
        flash('Producto eliminado del carrito.', 'success')
        return redirect(url_for('carrito'))
    else:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM producto WHERE id_producto = %s", (id,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()

        if producto:
            carrito[str(id)] = {
                'nombre': producto['nombre'],
                'precio': float(producto['precio']),
                'imagen': producto['imagen'],
                'cantidad': cantidad
            }

        session['carrito'] = carrito
        flash('Producto actualizado en el carrito.', 'success')
        return redirect(url_for('producto', nombre=producto['nombre']))


@app.route('/alta_producto', methods=['GET', 'POST'])
def alta_producto():
    if request.method == 'POST':
        # Abrimos conexión y cursor solo si es POST
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        imagen = request.form['imagen']
        tipo = request.form['tipo']
        precio = request.form['precio']

        cursor.execute("""
            INSERT INTO producto (nombre, descripcion, imagen, tipo, precio)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, descripcion, imagen, tipo, precio))

        conn.commit()
        cursor.close()
        conn.close()

        if tipo == 'fruta':
            return redirect(url_for('frutas'))
        else:
            return redirect(url_for('verduras'))

    return render_template('alta_producto.html')

@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM producto WHERE id_producto = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Producto eliminado correctamente", "success")
    return redirect(url_for('index'))

@app.route('/espacio_clientes')
def espacio_clientes():
    return render_template('espacio_clientes.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('index'))

@app.route('/pagar_carrito', methods=['POST'])
def pagar_carrito():
    modo = request.form.get('modo')
    carrito = session.get('carrito', {})

    if not carrito:
        flash("Tu carrito está vacío.", "danger")
        return redirect(url_for('carrito'))

    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())

    if modo == 'recoger':
        flash(f"¡Gracias por tu compra! Pasa a recoger tu pedido. Total: {total:.2f} €", "success")
    elif modo == 'domicilio':
        flash(f"¡Gracias por tu compra! Tu pedido será entregado a domicilio. Total: {total:.2f} €", "success")
    else:
        flash("Modo de pago no reconocido.", "danger")

   
    session['carrito'] = {}

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
