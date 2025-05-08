import asyncio  # Importa el módulo asyncio para manejar operaciones asíncronas
import websockets  # Importa el módulo websockets para manejar conexiones WebSocket
import json  # Importa el módulo json para trabajar con datos JSON
import psycopg2  # Importa el módulo psycopg2 para conectarse a una base de datos PostgreSQL
import logging  # Importa el módulo logging para registrar mensajes de log
import smtplib # Importa el módulo smtplib para enviar correos electrónicos
import subprocess  # Importa el módulo subprocess para ejecutar comandos del sistema
from email.message import EmailMessage  # Importa la clase EmailMessage para crear mensajes de correo electrónico
from datetime import datetime  # Importa la clase datetime para trabajar con fechas y horas
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash  # Importa varias funciones y clases de Flask para crear la aplicación web
from flask_bcrypt import Bcrypt  # Importa Bcrypt de Flask para manejar el hashing de contraseñas
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # Importa varias funciones y clases de Flask-Login para manejar la autenticación de usuarios
from websockets.server import serve  # Importa la función serve de websockets para iniciar el servidor WebSocket
import threading  # Importa el módulo threading para manejar hilos
import re  # Importa el módulo re para trabajar con expresiones regulares
import os
import psycopg2
from websockets import serve
from flask import Flask


# Crea una cola de mensajes para la comunicación entre Flask y WebSocket
message_queue = asyncio.Queue()

EMAIL_ADDRESS = 'saludcucei@gmail.com'  # ← pon aquí tu correo de Gmail
EMAIL_PASSWORD = 'ueys ybml nzta imki'  # ← y aquí tu contraseña de aplicación

from email.message import EmailMessage
# Configuración de log
logging.basicConfig(level=logging.INFO)  # Configura el nivel de log a INFO
logger = logging.getLogger(__name__)  # Crea un logger con el nombre del módulo actual

# Intenta obtener DATABASE_URL desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la URL de la base de datos desde Railway
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    cur = conn.cursor()
    logger.info("✅ Conexión a la base de datos exitosa")

    # Verificar tablas en la base de datos
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cur.fetchall()
    logger.info(f"📄 Tablas en la base de datos: {tables}")

except psycopg2.OperationalError as e:
    logger.error(f"❌ Error de conexión a PostgreSQL: {e}")
    conn = None

except Exception as e:
    logger.error(f"⚠️ Error inesperado: {e}")
    conn = None

finally:
    if conn:
        cur.close()
        conn.close()
        logger.info("🔄 Conexión cerrada correctamente")

def enviar_correo_bienvenida(destinatario, nombre_usuario, password):
    mensaje = EmailMessage()
    mensaje['Subject'] = '¡Bienvenido a nuestra plataforma!'
    mensaje['From'] = EMAIL_ADDRESS
    mensaje['To'] = destinatario

    # URL personalizada para recuperación de contraseña (puede ser un token más adelante)
    link_recuperacion = f'http://127.0.0.1:5000/update_password'

    mensaje.set_content(f"""
    Hola {nombre_usuario},

    ¡Gracias por registrarte en nuestra plataforma!

    Aquí tienes tus credenciales:
    👤 Usuario: {nombre_usuario}
    🔑 Contraseña: {password}

    En caso de que olvides tu contraseña, puedes restablecerla con el siguiente enlace:
    🔗 {link_recuperacion}

    ¡Esperamos que disfrutes del servicio!

    Saludos,
    """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(mensaje)
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def validate_email(email):
    allowed_domains = {"gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "@alumnos.udg.mx"}  # Dominios permitidos
    domain = email.split("@")[-1]

    if domain not in allowed_domains:
        raise ValueError(f"Solo se permiten correos de {', '.join(allowed_domains)}")
    
def validate_password(password):
    #"""Verifica que la contraseña cumpla con los requisitos de seguridad."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe incluir al menos una letra mayúscula.")
    
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("La contraseña debe incluir al menos un carácter especial.")

    return True

# Función para obtener las citas pendientes del día
def get_today_appointments():
    try:
        today = datetime.now().date()  # Obtiene la fecha actual
        estatus = 'pendiente'  # Define el estatus de las citas a buscar
        
        # Consulta que filtra las citas pendientes que no han pasado
        cur.execute("SELECT id, nombre_alumno, correo_alumno, departamento, hora, dia FROM citas WHERE dia = %s AND estatus = %s", (today, estatus))
        rows = cur.fetchall()  # Obtiene todas las filas resultantes de la consulta

        appointments = []  # Lista para almacenar las citas
        for row in rows:
            appointments.append({
                "id": row[0],  # ID de la cita
                "nombre_alumno": row[1],  # Nombre del alumno
                "correo_alumno": row[2],  # Correo del alumno
                "departamento": row[3],  # Departamento
                "hora": row[4].strftime('%H:%M'),  # Formato de hora HH:MM
                "dia": row[5].strftime('%Y-%m-%d')  # Formato de fecha YYYY-MM-DD
            })
        
        logger.info(f"Citas obtenidas: {appointments}")  # Registra las citas obtenidas
        return appointments  # Retorna la lista de citas
    except Exception as e:
        logger.error(f"Error al obtener las citas del día: {e}")  # Registra un mensaje de error si ocurre una excepción
        return []  # Retorna una lista vacía en caso de error
    
# Funcion para obtener el total de alumnos    
def get_total_alumnos():
    try:
        # Ejecuta una consulta SQL para contar el número total de alumnos en la tabla 'citas'
        cur.execute("SELECT COUNT(*) FROM citas")
        # Obtiene el resultado de la consulta
        total_alumnos = cur.fetchone()[0]
        # Registra el total de alumnos obtenidos
        logger.info(f"Total alumnos: {total_alumnos}")
        # Retorna el total de alumnos
        return total_alumnos
    except Exception as e:
        # Registra un mensaje de error si ocurre una excepción
        logger.error(f"Error al obtener el total de alumnos: {e}")
        # Retorna 0 en caso de error
        return 0

# Función para obtener los datos de los comentarios, incluyendo el total
def get_comment_data():
    try:
        # Ejecuta una consulta SQL para contar el número total de comentarios en la tabla 'comentarios'
        cur.execute("SELECT COUNT(*) FROM comentarios")
        # Obtiene el resultado de la consulta
        total_comments = cur.fetchone()[0]

        # Ejecuta una consulta SQL para contar el número de comentarios por sentimiento
        cur.execute("SELECT sentimiento, COUNT(*) FROM comentarios GROUP BY sentimiento")
        # Obtiene todas las filas resultantes de la consulta
        rows = cur.fetchall()
        
        # Inicializa un diccionario para almacenar los datos de los comentarios
        data = {
            "Positivos": 0,
            "Neutrales": 0,
            "Negativos": 0,
            "TotalComentarios": total_comments
        }

        # Itera sobre las filas obtenidas y actualiza el diccionario con los datos de los comentarios
        for row in rows:
            sentiment = row[0]
            count = row[1]
            if sentiment == "Positivo":
                data["Positivos"] = count
            elif sentiment == "Neutral":
                data["Neutrales"] = count
            elif sentiment == "Negativo":
                data["Negativos"] = count
        
        # Registra los datos obtenidos
        logger.info(f"Datos obtenidos: {data}")
        # Retorna el diccionario con los datos de los comentarios
        return data
    except Exception as e:
        # Registra un mensaje de error si ocurre una excepción
        logger.error(f"Error al obtener datos de la base de datos: {e}")
        # Retorna None en caso de error
        return None

# Aplicación Flask para gestión de citas y login
app = Flask(__name__)
# Configura la clave secreta para la aplicación Flask
app.config['SECRET_KEY'] = '214604219'

# Conexión WebSocket
clients = set()  # Lista de clientes conectados

# Inicializa Bcrypt para manejar el hashing de contraseñas
bcrypt = Bcrypt(app)
# Inicializa LoginManager para manejar la autenticación de usuarios
login_manager = LoginManager(app)
# Configura la vista de login
login_manager.login_view = 'login'

# Clase User que representa a un usuario
class User(UserMixin):
    
    def __init__(self, id, username, password, email=None, full_name=None, birthdate=None, phone=None, area=None):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.full_name = full_name
        self.birthdate = birthdate
        self.phone = phone
        self.area = area  

        

    @staticmethod
    def get_by_username(username):
        # Ejecuta una consulta SQL para obtener un usuario por su nombre de usuario
        cur.execute("""
                SELECT id, username, password, email, full_name, birthdate, phone, area 
                FROM usuarios WHERE username = %s
            """, (username,))        # Obtiene los datos del usuario
        user_data = cur.fetchone()
        # Si se encuentran datos del usuario, retorna una instancia de User
        if user_data:
            return User(*user_data)
        # Si no se encuentran datos del usuario, retorna None
        return None

    @staticmethod
    def get_by_id(user_id):
        # Ejecuta una consulta SQL para obtener un usuario por su ID
        cur.execute("SELECT id, username, password, email, full_name, birthdate, phone, area FROM usuarios WHERE id = %s", (user_id,))
        # Obtiene los datos del usuario
        user_data = cur.fetchone()
        # Si se encuentran datos del usuario, retorna una instancia de User
        if user_data:
            return User(*user_data)
        # Si no se encuentran datos del usuario, retorna None
        return None
    
    @staticmethod
    def get_by_email(email):
        cur.execute("SELECT id, username, password, email, full_name, birthdate, phone, area FROM usuarios WHERE email = %s", (email,))
        user_data = cur.fetchone()
        if user_data:
            return User(*user_data)
        return None


    @staticmethod
    def create(username, password, email):
        if not email.endswith("@gmail.com"):
            raise ValueError("El correo debe ser de Gmail")
        
        # Genera un hash de la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Ejecuta una consulta SQL para insertar un nuevo usuario en la base de datos
        cur.execute("INSERT INTO usuarios (username, password, email) VALUES (%s, %s, %s) RETURNING id", (username, hashed_password, email))
        # Obtiene el ID del nuevo usuario
        user_id = cur.fetchone()[0]
        # Confirma los cambios en la base de datos
        conn.commit()
        # Retorna una instancia de User con los datos del nuevo usuario
        return User(user_id, username, hashed_password)
    



@login_manager.user_loader
def load_user(user_id):
    user_data = User.get_by_id(user_id)  # Obtiene los datos del usuario por su ID
    if user_data is None:
        logger.error(f"Error al cargar el usuario con ID {user_id}: Datos del usuario no encontrados")  # Registra un error si no se encuentran datos del usuario
        return None  # Retorna None si no se encuentran datos del usuario
    return user_data  # Retorna los datos del usuario

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']  # Obtiene el nombre de usuario del formulario
        password = request.form['password']  # Obtiene la contraseña del formulario
        user = User.get_by_username(username)  # Obtiene el usuario por su nombre de usuario
        if user and bcrypt.check_password_hash(user.password, password):  # Verifica si el usuario existe y la contraseña es correcta
            login_user(user)  # Inicia sesión con el usuario
            return redirect(url_for('serve_index'))  # Redirige a la página principal
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')  # Muestra un mensaje de error si las credenciales son incorrectas
    return render_template('login.html')  # Renderiza la plantilla de inicio de sesión

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario
    flash('Has cerrado sesión', 'success')  # Muestra un mensaje de éxito
    return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        try:
            validate_email(email)  # Validar el email
            validate_password(password)  # Validar la contraseña
            
            # Verificar si el nombre de usuario ya existe
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                existing_user = cur.fetchone()
                if existing_user:
                    raise ValueError("El nombre de usuario ya está en uso, elige otro.")

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Si el nombre es único, proceder con la inserción
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (username, password, email) VALUES (%s, %s, %s) RETURNING id",
                    (username, hashed_password, email)
                )
                conn.commit()
                
            enviar_correo_bienvenida(destinatario=email, nombre_usuario=username, password=password)

            flash("Registro exitoso", "success")
            return redirect(url_for("register"))

        except ValueError as ve:
            flash(str(ve), "danger")  # Mensaje de error si el nombre de usuario ya está en uso

        except psycopg2.DatabaseError as db_err:
            conn.rollback()
            flash("Error de base de datos", "danger")

    return render_template("register.html")

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    birthdate = request.form.get('birthdate') or None
    phone = request.form.get('phone')
    area = request.form.get('area')

    try:
        cur.execute("""
            UPDATE usuarios 
            SET email = %s, full_name = %s, birthdate = %s, phone = %s, area = %s 
            WHERE id = %s
        """, (email, full_name, birthdate, phone, area, current_user.id))
        conn.commit()
        flash('Perfil actualizado correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error al actualizar el perfil.', 'danger')
        print(e)

    return redirect(url_for('profile'))


@app.route('/')
@login_required
def serve_index():
    return send_from_directory('.', 'index.html')  # Sirve el archivo index.html desde el directorio actual


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)  # Sirve archivos estáticos desde el directorio 'static'

@app.route('/profile')
@login_required
def profile():
    user_id = current_user.id

    # Obtener datos personales
    cur.execute("SELECT full_name, birthdate, phone, area, email FROM usuarios WHERE id = %s", (user_id,))
    user_details = cur.fetchone()

    # user_details será: (full_name, birthdate, phone, area, email)
    user_email = user_details[4]  # correo del usuario actual

    # Obtener citas pendientes según el correo y estatus
    cur.execute("""
        SELECT departamento, dia, hora
        FROM citas
        WHERE correo_alumno = %s AND estatus = 'pendiente'
        ORDER BY dia, hora
    """, (user_email,))
    citas = cur.fetchall()

    return render_template('profile.html', user=current_user, user_details=user_details, citas=citas)



@app.route('/citas', methods=['GET'])
@login_required
def get_citas():
    return render_template('citas.html')  # Renderiza la plantilla de citas

@app.route('/edit_profile')
@login_required
def edit_profile():
    return render_template('edit_profile.html', user=current_user)# Renderiza la plantilla de edición de perfil con los datos del usuario actual

@app.route('/inicio')
def inicio():
    return render_template('inicio.html', user=current_user)# Renderiza la plantilla de inicio

@app.route('/servicios')
def servicios():
    return render_template('servicios.html', user=current_user)# Renderiza la plantilla de servicios

@app.route('/consulta', methods=['GET'])
@login_required
def get_consulta():
    return render_template('consulta.html')  # Renderiza la plantilla de citas

@app.route('/psicologia', methods=['GET'])
@login_required
def get_psicologia():
    return render_template('psicologia.html')  # Renderiza la plantilla de citas

@app.route('/nutriologia', methods=['GET'])
@login_required
def get_nutriologia():
    return render_template('nutriologia.html')  # Renderiza la plantilla de citas

@app.route('/api/citas', methods=['GET'])
@login_required
def get_citas_data():
    try:
        cur.execute("SELECT id, nombre_alumno, apellidos, correo_alumno, codigo, departamento, hora, dia, estatus FROM citas")  # Ejecuta una consulta SQL para obtener todas las citas
        rows = cur.fetchall()  # Obtiene todas las filas resultantes de la consulta
        citas = []  # Lista para almacenar las citas
        for row in rows:
            hora = row[6]  # Obtiene la hora de la cita
            dia = row[7]  # Obtiene el día de la cita
            if isinstance(hora, str):
                hora = datetime.strptime(hora, '%H:%M:%S').time()  # Convierte la hora a un objeto time si es una cadena
            if isinstance(dia, str):
                dia = datetime.strptime(dia, '%Y-%m-%d').date()  # Convierte el día a un objeto date si es una cadena
            citas.append({
                'id': row[0],  # ID de la cita
                'nombre_alumno': row[1],  # Nombre del alumno
                'apellidos': row[2],  # Apellidos del alumno
                'correo_alumno': row[3],  # Correo del alumno
                'codigo': row[4],  # Código del alumno
                'departamento': row[5],  # Departamento
                'hora': hora.strftime('%H:%M'),  # Formato de hora HH:MM
                'dia': dia.strftime('%Y-%m-%d'),  # Formato de fecha YYYY-MM-DD
                'estatus': row[8]  # Estatus de la cita
            })
        return jsonify(citas)  # Retorna las citas en formato JSON
    except Exception as e:
        logger.error(f"Error al obtener las citas: {e}")  # Registra un mensaje de error si ocurre una excepción
        return jsonify({"error": "Error al obtener las citas"}), 500  # Retorna un mensaje de error en formato JSON

@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    if request.method == 'POST':
        current_password = request.form['current_password']  # Obtiene la contraseña actual del formulario
        new_password = request.form['new_password']  # Obtiene la nueva contraseña del formulario
        
        user = User.get_by_id(current_user.id)  # Obtiene los datos del usuario actual
        
        if user and bcrypt.check_password_hash(user.password, current_password):  # Verifica si la contraseña actual es correcta
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')  # Genera un hash de la nueva contraseña
            cur.execute("UPDATE usuarios SET password = %s WHERE id = %s", (hashed_password, user.id))  # Actualiza la contraseña en la base de datos
            conn.commit()  # Confirma los cambios en la base de datos
            flash('Contraseña actualizada exitosamente', 'success')  # Muestra un mensaje de éxito
            return redirect(url_for('serve_index'))  # Redirige a la página principal
        else:
            flash('Contraseña actual incorrecta', 'danger')  # Muestra un mensaje de error si la contraseña actual es incorrecta
    return render_template('update_password.html')  # Renderiza la plantilla de actualización de contraseña


@app.route('/profile_edit', methods=['GET'])
@login_required
def profile_edit():
    try:
        # Consulta para obtener citas pendientes del usuario actual
        cur.execute("SELECT departamento, dia, hora FROM citas WHERE codigo = %s AND estatus = 'pendiente'", (current_user.id,))
        citas = cur.fetchall()
        
        # Renderiza el template con la info del usuario y sus citas
        return render_template("profile.html", user=current_user, citas=citas)
    except Exception as e:
        print(f"Error al obtener citas: {e}")
        return render_template("profile.html", user=current_user, citas=[])

@app.route('/api/citas', methods=['POST'])
@login_required
def add_cita():
    data = request.json  # Obtiene los datos de la cita del cuerpo de la solicitud
    try:
        cur.execute("INSERT INTO citas (nombre_alumno, apellidos, correo_alumno, codigo, departamento, hora, dia, estatus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (data['nombre_alumno'], data['apellidos'], data['correo_alumno'], data['codigo'], data['departamento'], data['hora'], data['dia'], data['estatus']))  # Inserta una nueva cita en la base de datos
        conn.commit()  # Confirma los cambios en la base de datos
        return '', 204  # Retorna una respuesta vacía con el código de estado 204
    except Exception as e:
        logger.error(f"Error al agregar una cita: {e}")  # Registra un mensaje de error si ocurre una excepción
        return jsonify({"error": "Error al agregar una cita"}), 500  # Retorna un mensaje de error en formato JSON

@app.route('/api/citas/<int:id>', methods=['PUT'])
@login_required
def update_cita(id):
    data = request.json  # Obtiene los datos de la cita del cuerpo de la solicitud
    try:
        cur.execute("UPDATE citas SET nombre_alumno=%s, apellidos=%s, correo_alumno=%s, codigo=%s, departamento=%s, hora=%s, dia=%s, estatus=%s WHERE id=%s",
                    (data['nombre_alumno'], data['apellidos'], data['correo_alumno'], data['codigo'], data['departamento'], data['hora'], data['dia'], data['estatus'], id))  # Actualiza una cita existente en la base de datos
        conn.commit()  # Confirma los cambios en la base de datos
        return '', 204  # Retorna una respuesta vacía con el código de estado 204
    except Exception as e:
        logger.error(f"Error al actualizar la cita: {e}")  # Registra un mensaje de error si ocurre una excepción
        return jsonify({"error": "Error al actualizar la cita"}), 500  # Retorna un mensaje de error en formato JSON

@app.route('/api/citas/<int:id>', methods=['DELETE'])
@login_required
def delete_cita(id):
    try:
        cur.execute("DELETE FROM citas WHERE id=%s", (id,))  # Elimina una cita de la base de datos por su ID
        conn.commit()  # Confirma los cambios en la base de datos
        return '', 204  # Retorna una respuesta vacía con el código de estado 204
    except Exception as e:
        logger.error(f"Error al eliminar la cita: {e}")  # Registra un mensaje de error si ocurre una excepción
        return jsonify({"error": "Error al eliminar la cita"}), 500  # Retorna un mensaje de error en formato JSON

def actualizar_citas_periodicamente(intervalo):
    def ejecutar():
        logger.info("Ejecutando actualización de citas vencidas...")  # Registra un mensaje de información
        update_citas_vencidas()  # Llama a la función para actualizar las citas vencidas
        planificar()  # Planifica la próxima ejecución
    
    def planificar():
        logger.info(f"Planificando próxima actualización en {intervalo} segundos...")  # Registra un mensaje de información
        threading.Timer(intervalo, ejecutar).start()  # Inicia un temporizador para ejecutar la función después del intervalo especificado

    planificar()  # Planifica la primera ejecución

def update_citas_vencidas():
    try:
        now = datetime.now().time()  # Solo obtiene la hora actual
        today = datetime.now().date()  # Obtiene la fecha actual

        # Actualiza el estatus de las citas vencidas a 'completada'
        cur.execute("""
            UPDATE citas 
            SET estatus = 'completada' 
            WHERE hora < %s AND dia <= %s AND estatus = 'pendiente'
        """, (now, today))
        conn.commit()  # Confirma los cambios en la base de datos
        logger.info("Citas vencidas actualizadas a 'completada'")  # Registra un mensaje de éxito
    except Exception as e:
        logger.error(f"Error al actualizar citas vencidas: {e}")  # Registra un mensaje de error si ocurre una excepción

def get_user_appointments(user_id):
    try:
        cur.execute("SELECT departamento, dia, hora FROM citas WHERE codigo = %s AND estatus = 'pendiente'", (user_id,))
        rows = cur.fetchall()
        return [{"departamento": r[0], "dia": str(r[1]), "hora": str(r[2])} for r in rows]
    except Exception as e:
        logger.error(f"Error al obtener citas del usuario {user_id}: {e}")
        return []
    
@app.route('/api/comentarios', methods=['POST'])
def agregar_comentario():
    data = request.json
    comentario = data.get('comentario')

    if comentario:
        cur.execute("INSERT INTO comentarios (comentario) VALUES (%s)", (comentario,))
        conn.commit()

        # Ejecutar clasificación de comentarios
        subprocess.Popen(["python", "D:/Brandon/Modular1.0/traductor.py"])

        return jsonify({"message": "Comentario recibido y procesado"}), 200
    else:
        return jsonify({"error": "Comentario no proporcionado"}), 400

async def enviar_a_clientes(msg):
    for client in clients.copy():  # Copia para evitar modificaciones durante la iteración
        if client.open:  # Verificar que el cliente sigue conectado
            try:
                await client.send(msg)
            except Exception as e:
                print(f"Error enviando mensaje: {e}")
                clients.remove(client)  # Eliminar clientes desconectados



    
    
# Llama a esta función al iniciar la aplicación
update_citas_vencidas()
# Llama a la función para iniciar la planificación periódica con un intervalo de 5 minutos (300 segundos)
actualizar_citas_periodicamente(1200)


# Manejo de conexiones WebSocket
async def handle_connection(websocket, path):
    clients.add(websocket)  # Agrega el nuevo cliente a la lista de clientes conectados
    try:
        logger.info(f"Cliente conectado: {websocket.remote_address}")  # Registra la conexión de un cliente
        
        while True:
            await asyncio.sleep(1)  # Espera 1 segundo entre cada iteración
            comment_data = get_comment_data()  # Obtiene los datos de los comentarios
            appointments = get_today_appointments()  # Obtiene las citas pendientes del día
            total_alumnos = get_total_alumnos()  # Obtiene el total de alumnos

            response_data = {
                "comentarios": comment_data, 
                "citas": appointments,
                "total_alumnos": total_alumnos
            }  # Crea un diccionario con los datos obtenidos
            logger.info(f"Enviando datos actualizados: {response_data}")  # Registra los datos que se enviarán
            await websocket.send(json.dumps(response_data))  # Envía los datos al cliente en formato JSON
    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"Conexión cerrada con {websocket.remote_address}: {e}")  # Registra un aviso si la conexión se cierra
    except Exception as e:
        logger.error(f"Error en la conexión con el cliente {websocket.remote_address}: {e}")  # Registra un error si ocurre una excepción
    finally:
        logger.info(f"Conexión cerrada con {websocket.remote_address}")  # Registra el cierre de la conexión
        await websocket.close()  # Cierra la conexión WebSocket
# Función para enviar actualizaciones de comentarios o citas a todos los clientes conectados
async def notify_clients_new_comment():
    comment_data = get_comment_data()  # Obtiene los comentarios actualizados
    appointments = get_today_appointments()  # Obtiene las citas del día
    total_alumnos = get_total_alumnos()  # Obtiene el total de alumnos

    response_data = {
        "comentarios": comment_data,
        "citas": appointments,
        "total_alumnos": total_alumnos
    }

    # Enviar los datos a todos los clientes conectados
    for client in clients:
        await client.send(json.dumps(response_data))
async def start_websocket():
    server = await serve(handle_connection, "0.0.0.0", 8765)  # WebSocket en 8765
    print("✅ WebSocket corriendo en ws://0.0.0.0:8765")
    await server.wait_closed()

def websocket_thread():
    asyncio.run(start_websocket())  # Inicia WebSocket de forma bloqueante

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Flask en 8080
    threading.Thread(target=websocket_thread).start()  # WebSocket en hilo separado
    app.run(host="0.0.0.0", port=port)



# Cerrar la conexión a la base de datos al finalizar
cur.close()  # Cierra el cursor de la base de datos
conn.close()  # Cierra la conexión a la base de datos

