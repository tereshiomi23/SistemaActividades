from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion_actividades.db'
db = SQLAlchemy(app)

# Tu "Ficha" de registro (El Modelo)
class Actividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_programa = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    beneficiarios = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    cantidad_ayuda = db.Column(db.Integer)

# 1. Ruta para ver el formulario
@app.route('/')
def inicio():
    # render_template busca el archivo dentro de la carpeta /templates
    return render_template('index.html')

# 2. Ruta para recibir los datos del formulario
@app.route('/registrar', methods=['POST'])
def registrar():
    # Aquí es donde usamos los "nombres" que pusiste en el HTML
    programa = request.form.get('tipo_programa')
    actividad = request.form.get('descripcion')
    personas = request.form.get('beneficiarios')
    lugar = request.form.get('ubicacion')
    cantidad = request.form.get('cantidad_ayuda')
    
    # Por ahora, solo mostraremos un mensaje de confirmación
    return f"<h1>¡Datos recibidos!</h1><p>Registraste el programa {programa} con la actividad {actividad} para {personas} personas en {lugar}.</p>"

if __name__ == '__main__':
    app.run(debug=True)