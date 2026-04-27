import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'pequiven_sistema_seguro_2026'

# Configuración de carpetas (Base de datos y Fotos)
try:
    os.makedirs(app.instance_path)
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
except OSError:
    pass

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'gestion_actividades.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---

class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default='analista')

class Actividades(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_actividad = db.Column(db.Date, nullable=False)
    programa_gestion = db.Column(db.String(100), nullable=False)
    tipo_actividad = db.Column(db.String(100), nullable=False)
    nombre_institucion = db.Column(db.String(200), nullable=False)
    descripcion_actividad = db.Column(db.Text, nullable=False)
    personal_asistio = db.Column(db.Text, nullable=False)
    direccion = db.Column(db.Text, nullable=False)
    cantidad_beneficiarios = db.Column(db.Integer, default=0)
    
    # Campos para guardar los nombres de las imágenes
    foto1 = db.Column(db.String(255), nullable=True)
    foto2 = db.Column(db.String(255), nullable=True)
    foto3 = db.Column(db.String(255), nullable=True)

# --- FUNCIONES DE APOYO ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1).lower() in app.config['ALLOWED_EXTENSIONS']

# --- RUTAS ---

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        password = request.form['password']
        user = Usuarios.query.filter_by(nombre_usuario=usuario).first()
        if user and check_password_hash(user.password, password):
            session.update({'user_id': user.id, 'username': user.nombre_usuario, 'rol': user.rol})
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Procesamiento de las 3 imágenes
            nombres_fotos = []
            for i in range(1, 4):
                f = request.files.get(f'foto{i}')
                if f and f.filename != '' and allowed_file(f.filename):
                    # Nombre único: fecha_hora_numero_nombreoriginal.jpg
                    ext = f.filename.rsplit('.', 1).lower()
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{i}.{ext}")
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    nombres_fotos.append(filename)
                else:
                    nombres_fotos.append(None)

            nueva_acta = Actividades(
                usuario_id=session['user_id'],
                fecha_actividad=datetime.strptime(request.form['fecha_actividad'], '%Y-%m-%d'),
                programa_gestion=request.form['programa_gestion'],
                tipo_actividad=request.form['tipo_actividad'],
                nombre_institucion=request.form['nombre_institucion'],
                descripcion_actividad=request.form['descripcion_actividad'],
                personal_asistio=request.form['personal_asistio'],
                direccion=request.form['direccion'],
                cantidad_beneficiarios=int(request.form['cantidad_beneficiarios'] or 0),
                foto1=nombres_fotos,
                foto2=nombres_fotos,
                foto3=nombres_fotos
            )
            db.session.add(nueva_acta)
            db.session.commit()
            flash('Actividad y fotos guardadas con éxito', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')
            
    return render_template('index.html')

@app.route('/consultar')
def consultar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = Actividades.query.order_by(Actividades.fecha_actividad.desc())
    if session.get('rol') in ['administrador', 'gerente', 'admin']:
        actividades_list = query.all()
    else:
        actividades_list = query.filter_by(usuario_id=session['user_id']).all()
        
    return render_template('consultar.html', actividades=actividades_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- INICIALIZACIÓN ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Usuarios.query.filter_by(nombre_usuario='admin').first():
            db.session.add(Usuarios(
                nombre_usuario='admin', 
                password=generate_password_hash('admin123'), 
                rol='administrador'
            ))
            db.session.commit()

    app.run(debug=True, host='0.0.0.0', port=80)