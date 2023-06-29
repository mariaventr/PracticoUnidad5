from datetime import datetime
from flask import Flask, request, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db 
from models import Preceptor, Estudiante, Curso, Asistencia
		

@app.route('/')
def inicio():
	return render_template('inicio.html')

def validatePreceptor(correo, clave):
    completion = False
    usuario_actual = None
    usuario_actual = Preceptor.query.filter_by(correo=str(correo)).first()
    dbClave = usuario_actual.clave
    completion = check_password_hash(clave, dbClave)
    print(completion)
    if completion is not True:
        usuario_actual = None
    return usuario_actual


@app.route('/login_preceptor', methods=['GET', 'POST'])
def login_preceptor():
    error = None
    if request.method == 'POST':
        correo = request.form['correo']
        clave = generate_password_hash(request.form['clave'])
        usuario_actual = validatePreceptor(correo, clave)
        if usuario_actual is None:
            error = 'Correo o clave inválida. ¡Intente nuevamente!'
        else:
            return render_template('inicio_preceptor.html', usuario=usuario_actual)
    return render_template('login_preceptor.html', error=error)

@app.route('/login_padre')
def login_padre():
    return "Función de inicio de sesión para padres no disponible en este momento."


@app.route('/asistencia/<int:usuario_id>', methods=['GET', 'POST'])
def registrar_asistencia(usuario_id):
    cursos = Curso.query.filter_by(idpreceptor=int(usuario_id)).all()
    anios_cursos = [curso.anio for curso in cursos]
    division = [curso.division for curso in cursos]
    print(division)

    if request.method == 'POST':
        curso_id = request.form['anio']
        division = request.form['division']
        fecha = request.form['fecha']
        estudiantes = Estudiante.query.filter_by(idcurso=int(curso_id)).order_by(Estudiante.nombre, Estudiante.apellido).all()
        return render_template('cargar_asistencia.html', estudiantes=estudiantes, fecha=fecha, division=division, anio=curso_id)

    return render_template('asistencia.html', anios_cursos=anios_cursos, division=division)

@app.route('/guardar_asistencia', methods=['POST'])
def guardar_asistencia():
    fecha = request.form['fecha']
    division = request.form['division']
    anio = request.form['anio']

    # Obtener estudiantes desde la base de datos
    estudiantes = Estudiante.query.order_by(Estudiante.nombre, Estudiante.apellido).all()

    asistencias = []

    for estudiante in estudiantes:
        if estudiante.idcurso == int(anio):
            asistencia_key = f'asistencia-{estudiante.id}'
            justificacion_key = f'justificacion-{estudiante.id}'
            asistencia = request.form.get(asistencia_key, '')
            justificacion = request.form.get(justificacion_key, '')
            asistencias.append((estudiante.id, asistencia, justificacion))

    for asistencia in asistencias:
        estudiante_id, asistio, justificacion = asistencia
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
        asistencia_obj = Asistencia(fecha=fecha_obj, codigoclase=division, asistio=asistio, justificacion=justificacion, idestudiante=estudiante_id)
        db.session.add(asistencia_obj)

    db.session.commit()

    return render_template("guardar_asistencia.html")



@app.route('/informe_detallado/<int:usuario_id>', methods=['GET', 'POST'])
def informe_detallado(usuario_id):
    informe = []
    cursos = Curso.query.filter_by(idpreceptor=usuario_id).all()

    if request.method == 'POST':
        curso_id = request.form['anio']
        print(curso_id)
        estudiantes = Estudiante.query.filter_by(idcurso=int(curso_id)).order_by(Estudiante.nombre, Estudiante.apellido).all()
        for estudiante in estudiantes:
            asistencias = Asistencia.query.filter_by(idestudiante=int(estudiante.id)).all()
            asistencias_aula = sum(1 for asistencia in asistencias if asistencia.asistio == 's' and asistencia.codigoclase == 1)
            asistencias_educacion_fisica = sum(1 for asistencia in asistencias if asistencia.asistio == 's' and asistencia.codigoclase == 2)
            ausencias_justificadas_aula = sum(1 for asistencia in asistencias if asistencia.asistio == 'n' and asistencia.codigoclase == 1 and asistencia.justificacion != "")
            ausencias_injustificadas_aula = sum(1 for asistencia in asistencias if asistencia.asistio == 'n' and asistencia.codigoclase == 1 and asistencia.justificacion == "")
            ausencias_justificadas_educacion_fisica = sum(1 for asistencia in asistencias if asistencia.asistio == 'n' and asistencia.codigoclase == 2 and asistencia.justificacion != "")
            ausencias_injustificadas_educacion_fisica = sum(1 for asistencia in asistencias if asistencia.asistio == 'n' and asistencia.codigoclase == 2 and asistencia.justificacion == "")
            total_inasistencias = ausencias_injustificadas_aula + (ausencias_injustificadas_educacion_fisica * 0.5)
            informe.append({
                'estudiante': estudiante,
                'asistencias_aula': asistencias_aula,
                'asistencias_educacion_fisica': asistencias_educacion_fisica,
                'ausencias_justificadas_aula': ausencias_justificadas_aula,
                'ausencias_injustificadas_aula': ausencias_injustificadas_aula,
                'ausencias_justificadas_educacion_fisica': ausencias_justificadas_educacion_fisica,
                'ausencias_injustificadas_educacion_fisica': ausencias_injustificadas_educacion_fisica,
                'total_inasistencias': total_inasistencias
            })
        return render_template('informe.html', estudiantes=estudiantes, informe=informe)

    return render_template('informe_detallado.html', cursos=cursos)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
	
