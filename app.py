from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
from flask import send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sistema'

mysql = MySQL(app)

# Ruta donde se almacenarán las fotos
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploads/<nombreFoto>')
def uploads(nombreFoto):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nombreFoto)

@app.route('/')
def index():
    # Consulta SQL para obtener todos los empleados
    sql = "SELECT * FROM empleados;"
    
    # Establecer la conexión y ejecutar la consulta
    cursor = mysql.connection.cursor()
    cursor.execute(sql)
    
    # Obtener todos los resultados
    empleados = cursor.fetchall()
    
    # Cerrar el cursor
    cursor.close()
    
    # Pasar los datos de empleados a la plantilla
    return render_template('empleados/index.html', empleados=empleados)

@app.route('/destroy/<int:id>')
def destroy(id):
    cursor = mysql.connection.cursor()

    # Obtener la foto del empleado antes de eliminarlo
    cursor.execute("SELECT foto FROM empleados WHERE id=%s", (id,))
    empleado = cursor.fetchone()
    foto_actual = empleado[0]

    # Borrar el empleado
    cursor.execute("DELETE FROM empleados WHERE id=%s", (id,))
    mysql.connection.commit()

    # Borrar la foto del directorio uploads si existe
    if foto_actual:
        ruta_foto = os.path.join(app.config['UPLOAD_FOLDER'], foto_actual)
        if os.path.exists(ruta_foto):
            os.remove(ruta_foto)

    cursor.close()
    return redirect('/')
@app.route('/edit/<int:id>')
def edit(id):
    # Establecer el cursor para ejecutar la consulta
    cursor = mysql.connection.cursor()

    # Ejecutar la consulta para obtener el empleado con el ID proporcionado
    cursor.execute("SELECT * FROM empleados WHERE id=%s", (id,))
    empleado = cursor.fetchone()  # Usamos fetchone() para obtener un solo registro

    # Cerrar el cursor
    cursor.close()

    # Verificar si se encontró el empleado
    if empleado is None:
        return "Empleado no encontrado", 404

    # Renderizar la plantilla edit.html con los datos del empleado
    return render_template('empleados/edit.html', empleado=empleado)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    _nombre = request.form['txtNombre']
    _correo = request.form['txtCorreo']
    _foto = request.files['txtFoto']

    # Validación básica
    if _nombre == '' or _correo == '':
        return "Faltan datos", 400

    cursor = mysql.connection.cursor()

    # Obtener la foto actual antes de actualizar
    cursor.execute("SELECT foto FROM empleados WHERE id=%s", (id,))
    empleado = cursor.fetchone()
    foto_actual = empleado[0]

    # Actualizar los datos del empleado
    if _foto:
        nombre_foto = secure_filename(_foto.filename)

        # Borrar la foto anterior si existe
        if foto_actual:
            ruta_foto_actual = os.path.join(app.config['UPLOAD_FOLDER'], foto_actual)
            if os.path.exists(ruta_foto_actual):
                os.remove(ruta_foto_actual)

        # Guardar la nueva foto
        _foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))

        # Actualizar con la nueva foto
        cursor.execute("""
            UPDATE empleados
            SET nombre=%s, correo=%s, foto=%s
            WHERE id=%s
        """, (_nombre, _correo, nombre_foto, id))
    else:
        cursor.execute("""
            UPDATE empleados
            SET nombre=%s, correo=%s
            WHERE id=%s
        """, (_nombre, _correo, id))

    mysql.connection.commit()
    cursor.close()

    return redirect('/')
@app.route('/create')
def create():
    return render_template('empleados/create.html')

@app.route('/store', methods=['POST'])
def storage():
    # Capturando los datos del formulario
    _nombre = request.form['txtNombre']
    _correo = request.form['txtCorreo']
    _foto = request.files['txtFoto']

    # Validación simple
    if _nombre == '' or _correo == '' or _foto == '':
        return "Faltan datos en el formulario."

    # Guardar la foto en la carpeta de uploads
    nombre_foto = secure_filename(_foto.filename)
    _foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))

    # Consulta SQL parametrizada para evitar inyecciones
    sql = "INSERT INTO empleados (nombre, correo, foto) VALUES (%s, %s, %s);"
    datos = (_nombre, _correo, nombre_foto)

    # Ejecutar la consulta
    cursor = mysql.connection.cursor()
    cursor.execute(sql, datos)
    mysql.connection.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)