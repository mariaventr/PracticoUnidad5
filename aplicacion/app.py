from datetime import datetime
from flask import Flask, request, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db 
from models import Preceptor
		

@app.route('/')
def inicio():
	return render_template('inicio.html')
'''
@app.route('/nuevo_usuario', methods = ['GET','POST'])
def nuevo_usuario():   
	if request.method == 'POST':
		if not request.form['nombre'] or not request.form['email'] or not request.form['password']:
			return render_template('error.html', error="Los datos ingresados no son correctos...")
		else:
			nuevo_usuario = Preceptor(nombre=request.form['nombre'], apellido=request.form['apellido'], correo = request.form['email'], clave=generate_password_hash(request.form['password']))       
			db.session.add(nuevo_usuario)
			db.session.commit()
			return render_template('aviso.html', mensaje="El usuario se registró exitosamente")
	return render_template('nuevo_usuario.html')
'''

def validatePreceptor(correo, clave):
    con = sqlite3.connect('datos.db')
    completion = False
    usuario_actual = None
    with con:
        cur = con.cursor()
        cur.execute("SELECT correo, clave, nombre, id, apellido FROM preceptor")
        rows = cur.fetchall()
        for row in rows:
            dbCorreo = row[0]
            dbClave = row[1]
            if dbCorreo == correo:
                completion = check_password_hash(clave, dbClave)
                if completion:
                    usuario_actual = Preceptor.query.filter_by(id=row[3]).first()
                    db.session.commit()
                    if usuario_actual is None:
                        usuario_actual = Preceptor(id=row[3], nombre=row[2], apellido=row[4], correo=correo, clave=clave)
                        db.session.add(usuario_actual)
                        db.session.commit()
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
    con = sqlite3.connect('datos.db')
    with con:
        cur = con.cursor()
        cur.execute("SELECT id, anio, division FROM curso WHERE idpreceptor=?", (usuario_id,))
        rows = cur.fetchall()
        cursos= [row[1] for row in rows]
        division= [row[2] for row in rows]

    if request.method == 'POST':
        curso_id = request.form['anio']
        division = request.form['division']
        fecha = request.form['fecha']
        cur.execute("SELECT id, nombre, apellido,dni, idcurso,idpadre FROM estudiante WHERE idcurso=? ORDER BY nombre, apellido", (curso_id,))
        estudiantes = cur.fetchall()

        return render_template('cargar_asistencia.html', estudiantes=estudiantes, fecha=fecha, division=division, anio=curso_id)

    return render_template('asistencia.html', anios_cursos=cursos, division=division)

@app.route('/guardar_asistencia', methods=['POST'])
def guardar_asistencia():
    fecha = request.form['fecha']
    division = request.form['division']
    anio=request.form['anio']

    # Obtener estudiantes desde la base de datos
    con = sqlite3.connect('datos.db')
    cur = con.cursor()
    cur.execute("SELECT id, nombre, apellido, idcurso FROM estudiante ORDER BY nombre, apellido")
    estudiantes = cur.fetchall()
    con.close()

    asistencias = []

    for estudiante in estudiantes:
        if int(estudiante[3]) == int(anio):
            estudiante_id = estudiante[0]
            asistencia_key = f'asistencia-{estudiante_id}'
            justificacion_key = f'justificacion-{estudiante_id}'
            asistencia = request.form.get(asistencia_key, '')
            justificacion = request.form.get(justificacion_key, '')
            asistencias.append((estudiante_id, asistencia, justificacion))

    con = sqlite3.connect('datos.db')
    cur = con.cursor()
    for asistencia in asistencias:
        estudiante_id, asistio, justificacion = asistencia
        cur.execute("INSERT INTO asistencia (fecha, codigoclase, asistio, justificacion, idestudiante) VALUES (?, ?, ?, ?, ?)",
                    (fecha, division, asistio, justificacion, estudiante_id))

    con.commit()
    con.close()

    return render_template("guardar_asistencia.html")



@app.route('/informe_detallado/<int:usuario_id>', methods=['GET', 'POST'])
def informe_detallado(usuario_id):
    informe = []
    con = sqlite3.connect('datos.db')
    with con:
        cur = con.cursor()
        cur.execute("SELECT id, anio FROM curso WHERE idpreceptor=?", (usuario_id,))
        rows = cur.fetchall()
        cursos = [row[1] for row in rows]

        if request.method == 'POST':
            curso_id = request.form['anio']

            cur.execute("SELECT id, nombre, apellido, dni, idcurso, idpadre FROM estudiante WHERE idcurso=? ORDER BY nombre, apellido", (curso_id,))
            estudiantes = cur.fetchall()

            for estudiante in estudiantes:
                cur.execute("SELECT id, fecha, codigoclase,asistio, justificacion,idestudiante  FROM asistencia WHERE idestudiante=?", (estudiante[0],))
                asistencias = cur.fetchall()
                asistencias_aula = sum(1 for asistencia in asistencias if asistencia[3] == 's' and asistencia[2] == 1)
                asistencias_educacion_fisica = sum(1 for asistencia in asistencias if asistencia[3] == 's' and asistencia[2] == 2)
                ausencias_justificadas_aula = sum(1 for asistencia in asistencias if asistencia[3] == 'n' and asistencia[2] == 1 and asistencia[4] != "")
                ausencias_injustificadas_aula = sum(1 for asistencia in asistencias if asistencia[3] == 'n' and asistencia[2] == 1 and asistencia[4] == "")
                ausencias_justificadas_educacion_fisica = sum(1 for asistencia in asistencias if asistencia[3] == 'n' and asistencia[2] == 2 and asistencia[4] != "")
                ausencias_injustificadas_educacion_fisica = sum(1 for asistencia in asistencias if asistencia[3] == 'n' and asistencia[2] == 2 and asistencia[4] == "")
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
    
        return render_template('informe_detallado.html', anios_cursos=cursos)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
	