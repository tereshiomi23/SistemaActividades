import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Clave para cifrar las sesiones y mensajes flash
app.secret_key = 'pequiven_sistema_seguro_2026'

# --- 1. CONFIGURACIÓN ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion_actividades.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Crear carpeta de fotos si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# --- 2. MODELOS DE BASE DE DATOS ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False) # admin, gerente, coordinador, analista, planificador

class Actividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10))
    tipo_programa = db.Column(db.String(100))
    tipo_actividad = db.Column(db.String(100))
    coordinacion = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    beneficiarios = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    tipo_ayuda = db.Column(db.String(100))
    cantidad_ayuda = db.Column(db.Integer)
    foto = db.Column(db.String(200))
    usuario_creador = db.Column(db.String(50)) # Rastreo de quién cargó el dato

# --- 3. RUTAS DE SESIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['rol'] = user.rol
            session['username'] = user.username
            flash(f'Bienvenido/a {user.username}', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrecta', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- 4. RUTAS PRINCIPALES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    file = request.files.get('foto')
    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    try:
        nueva = Actividad(
            fecha=request.form.get('fecha'),
            tipo_programa=request.form.get('tipo_programa'),
            tipo_actividad=request.form.get('tipo_actividad'),
            coordinacion=request.form.get('coordinacion'),
            descripcion=request.form.get('descripcion'),
            beneficiarios=int(request.form.get('beneficiarios') or 0),
            ubicacion=request.form.get('ubicacion'),
            tipo_ayuda=request.form.get('tipo_ayuda'),
            cantidad_ayuda=int(request.form.get('cantidad_ayuda') or 0),
            foto=filename,
            usuario_creador=session['username']
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Registro guardado correctamente 🚀', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/consultar')
def consultar():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    # Mostramos todos los registros ordenados por el más reciente
    actividades = Actividad.query.order_by(Actividad.id.desc()).all()
    return render_template('consultar.html', actividades=actividades)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    # Solo el Administrador tiene permiso para borrar datos
    if session.get('rol') != 'admin':
        flash('Acceso denegado: Solo el Administrador puede eliminar registros', 'danger')
        return redirect(url_for('consultar'))
    
    act = Actividad.query.get_or_404(id)
    
    # Borrar la foto del servidor si existe para ahorrar espacio
    if act.foto:
        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], act.foto)
        if os.path.exists(foto_path):
            os.remove(foto_path)

    db.session.delete(act)
    db.session.commit()
    flash('Registro eliminado del sistema', 'success')
    return redirect(url_for('consultar'))

# --- 5. INICIO DE LA APP Y CREACIÓN DE USUARIOS ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Crear el usuario Admin si la tabla está vacía
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin', 
                rol='admin', 
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            
            # Ejemplo para un Analista
            analista = Usuario(
                username='analista1', 
                rol='analista', 
                password=generate_password_hash('analista2026')
            )
            db.session.add(analista)
            
            db.session.commit()
            print("Base de datos inicializada con usuarios: admin y analista1")
            

# El puerto 80 es el estándar de la web y suele saltarse bloqueos básicos
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
