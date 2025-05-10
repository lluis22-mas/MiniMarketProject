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
@app.route('/') # Ruta principal
def index():
    return render_template('index.html')

@app.route('/verduras') # Ruta para verduras
def verduras():
    conn = get_db_connection() # Conexión a la base de datos
    cursor = conn.cursor(dictionary=True) # Cursor para obtener resultados como diccionario
    cursor.execute("SELECT * FROM producto WHERE tipo = 'verdura'") # Consulta SQL para obtener verduras
    verduras = cursor.fetchall() # Obtener todas las verduras
    cursor.close()
    conn.close()
    return render_template('verduras.html', productos=verduras)

@app.route('/frutas') # Ruta para frutas
def frutas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM producto WHERE tipo = 'fruta'")
    frutas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('frutas.html', productos=frutas)

@app.route('/producto/<nombre>') # Ruta para un producto específico
def producto(nombre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM producto WHERE nombre = %s", (nombre,)) # Consulta SQL para obtener el producto por nombre
    producto = cursor.fetchone()


    while cursor.nextset(): # Limpiar el conjunto de resultados
        pass

    cursor.close()
    conn.close()

    if not producto: # Si no se encuentra el producto
        return "Producto no encontrado", 404

    return render_template('producto.html', producto=producto)


@app.route('/recetas') # Ruta para recetas
def recetas():
    return render_template('recetas.html')

@app.route('/quienessomos') # Ruta para "Quiénes somos"
def quienessomos():
    return render_template('quienessomos.html')

@app.route('/faq') # Ruta para preguntas frecuentes
def faq():
    return render_template('faq.html')

@app.route('/login', methods=['GET', 'POST']) # Ruta para login
def login():
    if request.method == 'POST': # Si se envía el formulario
        email = request.form['email'] # Obtener email
        password = request.form['password'] # Obtener contraseña

        conn = get_db_connection() # Conexión a la base de datos
        cursor = conn.cursor(dictionary=True) # Cursor para obtener resultados como diccionario
        cursor.execute("SELECT * FROM cliente WHERE email = %s AND password = %s", (email, password)) # Consulta SQL para verificar el usuario
        usuario = cursor.fetchone() # Obtener el usuario
        cursor.close()
        conn.close()

        if usuario: # Si se encuentra el usuario
            session['usuario'] = usuario['nombre'] # Guardar nombre en sesión
            session['email'] = usuario['email'] # Guardar email en sesión
            session['apellido'] = usuario['apellido'] # Guardar apellido en sesión
            session['telefono'] = usuario['telefono']   # Guardar teléfono en sesión
            session['direccion'] = usuario['direccion'] # Guardar dirección en sesión
            flash(f"Bienvenido, {usuario['nombre']}!", "success")   # Mensaje de bienvenida
            return redirect(url_for('index'))
        else:   # Si no se encuentra el usuario
            flash("Credenciales incorrectas", "danger")

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])    # Ruta para registro
def registro():
    if request.method == 'POST':    # Si se envía el formulario
        nombre = request.form['nombre']     # Obtener nombre
        apellido = request.form['apellido']   # Obtener apellido
        email = request.form['email']   # Obtener email
        telefono = request.form['telefono']   # Obtener teléfono
        direccion = request.form['direccion']   # Obtener dirección
        password = request.form['password']  # Obtener contraseña

        conn = get_db_connection()
        cursor = conn.cursor()
        try:  # Intentar insertar el nuevo usuario
            cursor.execute("""
                INSERT INTO cliente (nombre, apellido, email, telefono, direccion, password) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, apellido, email, telefono, direccion, password)) # Consulta SQL para insertar el nuevo usuario
            conn.commit()
            flash("Usuario registrado con éxito", "success")    # Mensaje de éxito
            return redirect(url_for('login'))   # Redirigir a la página de login
        except mysql.connector.Error as e:  # Manejar errores de MySQL
            flash(f"Error al registrar: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('registro.html')

@app.route('/carrito')  # Ruta para el carrito
def carrito():
    carrito = session.get('carrito', {})    # Obtener el carrito de la sesión
    productos = []  # Lista para almacenar los productos
    total = 0   # Inicializar total

    for producto_id, item in carrito.items():   # Iterar sobre los productos en el carrito
        subtotal = item['precio'] * item['cantidad']    # Calcular subtotal
        total += subtotal
        productos.append({
            'id': int(producto_id), # Convertir ID a entero
            'nombre': item['nombre'],   # Obtener nombre
            'precio': item['precio'],   # Obtener precio
            'imagen': item['imagen'],   # Obtener imagen
            'cantidad': item['cantidad'],   # Obtener cantidad
            'subtotal': subtotal    # Obtener subtotal
        })


    return render_template('carrito.html', productos=productos, total=total)

@app.route('/agregar_carrito/<int:id>', methods=['POST'])   # Ruta para agregar productos al carrito
def agregar_carrito(id):
    cantidad = int(request.form.get('cantidad', 1)) # Obtener cantidad del formulario

    if 'carrito' not in session:    # Si no hay carrito en la sesión
        session['carrito'] = {}   # Inicializar carrito

    carrito = session['carrito']    # Obtener carrito de la sesión

    if cantidad == 0:   # Si la cantidad es 0, eliminar el producto del carrito
        carrito.pop(str(id), None)
        session['carrito'] = carrito
        flash('Producto eliminado del carrito.', 'success') # Mensaje de éxito
        return redirect(url_for('carrito'))
    else:   # Si la cantidad es mayor a 0, agregar o actualizar el producto en el carrito
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)   # Cursor para obtener resultados como diccionario
        cursor.execute("SELECT * FROM producto WHERE id_producto = %s", (id,))  # Consulta SQL para obtener el producto por ID
        producto = cursor.fetchone()    # Obtener el producto
        cursor.close()
        conn.close()

        if producto:    # Si se encuentra el producto
            carrito[str(id)] = {    # Crear o actualizar el producto en el carrito
                'nombre': producto['nombre'],
                'precio': float(producto['precio']),
                'imagen': producto['imagen'],
                'cantidad': cantidad
            }

        session['carrito'] = carrito    # Guardar el carrito en la sesión
        flash('Producto actualizado en el carrito.', 'success') # Mensaje de éxito
        return redirect(url_for('producto', nombre=producto['nombre']))


@app.route('/alta_producto', methods=['GET', 'POST'])   # Ruta para agregar un nuevo producto
def alta_producto():
    if request.method == 'POST':    # Si se envía el formulario
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
        """, (nombre, descripcion, imagen, tipo, precio))   # Consulta SQL para insertar el nuevo producto

        conn.commit()
        cursor.close()
        conn.close()

        if tipo == 'fruta':   # Si el tipo es fruta
            return redirect(url_for('frutas'))
        else:   # Si el tipo es verdura
            return redirect(url_for('verduras'))

    return render_template('alta_producto.html')

@app.route('/eliminar_producto/<int:id>', methods=['POST']) # Ruta para eliminar un producto
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM producto WHERE id_producto = %s", (id,))    # Consulta SQL para eliminar el producto por ID
    conn.commit()
    cursor.close()
    conn.close()
    flash("Producto eliminado correctamente", "success")    # Mensaje de éxito
    return redirect(url_for('index'))

@app.route('/espacio_clientes') # Ruta para el espacio de clientes
def espacio_clientes():
    return render_template('espacio_clientes.html')

@app.route('/logout')  # Ruta para cerrar sesión
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('index'))

@app.route('/pagar_carrito', methods=['POST'])  # Ruta para pagar el carrito
def pagar_carrito():
    modo = request.form.get('modo') # Obtener modo de pago
    carrito = session.get('carrito', {})    # Obtener carrito de la sesión

    if not carrito: # Si el carrito está vacío
        flash("Tu carrito está vacío.", "danger")   # Mensaje de error
        return redirect(url_for('carrito'))

    total = sum(item['precio'] * item['cantidad'] for item in carrito.values()) # Calcular total

    if modo == 'recoger':   # Si el modo es recoger
        flash(f"¡Gracias por tu compra! Pasa a recoger tu pedido. Total: {total:.2f} €", "success")     
    elif modo == 'domicilio':   # Si el modo es domicilio
        flash(f"¡Gracias por tu compra! Tu pedido será entregado a domicilio. Total: {total:.2f} €", "success")
    else:   # Si el modo no es reconocido
        flash("Modo de pago no reconocido.", "danger")

   
    session['carrito'] = {}

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
