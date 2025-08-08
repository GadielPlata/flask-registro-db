from flask import Flask, request, render_template, jsonify
import psycopg2
from flask_cors import CORS
app = Flask(__name__)

# Configura tu conexión
conn = psycopg2.connect(
    host="localhost",
    database="veterinaria",
    user="postgres",
    password="1234"
)
cur = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')
cursor = conn.cursor()

@app.route('/ejecutar_consulta', methods=['POST'])
def ejecutar_consulta():
    data = request.get_json()
    query = data.get('query')

    try:
        cur.execute(query)

        # Si es una consulta SELECT, retornamos resultados
        if query.strip().lower().startswith('select'):
            columnas = [desc[0] for desc in cur.description]
            resultados = cur.fetchall()
            resultado_json = [dict(zip(columnas, fila)) for fila in resultados]
            return jsonify({"resultado": resultado_json})
        else:
            # Si es una consulta de acción (INSERT, UPDATE, DELETE)
            conn.commit()
            return jsonify({"resultado": []})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)})

@app.route('/citas')
def citas():
    return render_template('citas.html')  # Asegúrate de crear el archivo citas.html
@app.route("/inventario")
def inventario():
    return render_template("inventario.html")
@app.route('/ver_producto', methods=['POST'])
def ver_producto():
    data = request.get_json()
    id_producto = data.get('id_producto')
    try:
        cur.execute("SELECT * FROM Producto WHERE id_prod = %s", (id_producto,))
        producto = cur.fetchone()
        if producto:
            keys = [desc[0] for desc in cur.description]
            resultado = dict(zip(keys, producto))
            return jsonify(resultado)
        else:
            return jsonify({"error": "Producto no encontrado"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/eliminar_producto', methods=['POST'])
def eliminar_producto():
    data = request.get_json()
    id_producto = data.get('id_producto')
    try:
        cur.execute("DELETE FROM Producto WHERE id_prod = %s RETURNING id_prod", (id_producto,))
        eliminado = cur.fetchone()
        if eliminado:
            conn.commit()
            return jsonify({"mensaje": f"Producto con ID {id_producto} eliminado correctamente"})
        else:
            return jsonify({"error": "Producto no encontrado"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)})


@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    data = request.get_json()
    nombre = data.get('nombre')
    precio = data.get('precio')
    marca = data.get('marca')
    stock = data.get('stock')
    id_mov = data.get('id_mov')

    try:
        cur.execute(
            "INSERT INTO Producto (nombre, precio, marca, stock, id_mov) VALUES (%s, %s, %s, %s, %s)",
            (nombre, precio, marca, stock, id_mov)
        )
        conn.commit()
        return jsonify({"mensaje": "Producto agregado con éxito"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
@app.route('/agregar_movimiento', methods=['POST'])
def agregar_movimiento():
    data = request.get_json()
    tipo = data.get('tipo')
    cantidad = data.get('cantidad')
    fecha = data.get('fecha')
    id_admin = data.get('id_admin')
    id_vacuna = data.get('id_vacuna')
    id_tratamiento = data.get('id_tratamiento')

    try:
        cur.execute(
            "INSERT INTO Movimiento_Inventario (tipo, cantidad, fecha, id_admin, id_vacuna, id_tratamiento) VALUES (%s, %s, %s, %s, %s, %s)",
            (tipo, cantidad, fecha, id_admin, id_vacuna, id_tratamiento)
        )
        conn.commit()
        return jsonify({"mensaje": "Movimiento agregado con éxito"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/texto_movimiento")
def texto_movimiento():
    try:
        cur.execute("SELECT texto_movimiento();")
        resultado = cur.fetchone()[0]
        return jsonify({"texto": resultado})
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------- RUTA: TEXTO PRODUCTOS ----------
@app.route("/texto_producto")
def texto_producto():
    try:
        cur.execute("SELECT texto_producto();")
        resultado = cur.fetchone()[0]
        return jsonify({"texto": resultado})
    except Exception as e:
        return jsonify({"error": str(e)})

# Ruta para insertar una nueva cita
@app.route('/agendar_cita', methods=['POST'])
def agendar_cita():
    data = request.get_json()
    id_mascota = data.get('id_mascota')
    id_servicio = data.get('id_servicio')
    fecha = data.get('fecha')
    hora = data.get('hora')

    try:
        cur.execute(
            "INSERT INTO Agenda (id_mascota, id_servicio, fecha, hora) VALUES (%s, %s, %s, %s)",
            (id_mascota, id_servicio, fecha, hora)
        )
        conn.commit()
        return jsonify({"mensaje": "Cita agendada con éxito"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para llamar al procedimiento almacenado
@app.route('/texto_agenda', methods=['GET'])
def texto_agenda():
    try:
        cur.execute("SELECT * from texto_agenda();")   # Llamas la función
        resultado = cur.fetchone()               # Trae una sola fila (el texto)
        texto = resultado[0] if resultado else ''  # Extraes el texto o cadena vacía
        return jsonify({"texto": texto}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/buscar_historial', methods=['POST'])
def buscar_historial():
    id_mascota = request.json['id_mascota']

    cur = conn.cursor()

    # Tratamientos
    cur.execute("""
        SELECT t.id_tratamiento, t.observaciones, t.fecha_ini, t.fecha_fin
        FROM Historial h
        JOIN Tratamiento t ON h.id_historial = t.id_historial
        WHERE h.id_mascota = %s
    """, (id_mascota,))
    tratamientos = cur.fetchall()

    # Servicios
    cur.execute("""
        SELECT s.id_servicio, s.precio,
               v.nombre AS vacuna,
               p.tipo_corte,
               c.tipo AS tipo_cirugia
        FROM Historial h
        JOIN Contiene co ON h.id_historial = co.id_historial
        JOIN Servicio s ON co.id_servicio = s.id_servicio
        LEFT JOIN Vacunatorio v ON s.id_servicio = v.id_vacuna
        LEFT JOIN Peluqueria p ON s.id_servicio = p.id_peluqueria
        LEFT JOIN Cirugia c ON s.id_servicio = c.id_cirugia
        WHERE h.id_mascota = %s
    """, (id_mascota,))
    servicios = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "tratamientos": tratamientos,
        "servicios": servicios
    })

@app.route('/listar/propietarios')
def listar_propietarios():
    cur = conn.cursor()
    cur.execute("SELECT * FROM Propietario")
    datos = cur.fetchall()
    cur.close()
    return jsonify([["CI", "Nombre", "Apellido","Direccion","Telefono","Correo"]] + datos)

@app.route('/listar/mascotas')
def listar_mascotas():
    cur = conn.cursor()
    cur.execute("SELECT * FROM Mascota")
    datos = cur.fetchall()
    cur.close()
    return jsonify([["ID","Edad", "Nombre", "Especie","Raza","Color","Sexo","Propietario"]] + datos)

@app.route('/listar/servicios')
def listar_servicios():
    cur = conn.cursor()
    cur.execute("SELECT s.id_servicio, s.precio, v.nombre, p.tipo_corte, c.tipo FROM Servicio s "
                "LEFT JOIN Vacunatorio v ON s.id_servicio = v.id_vacuna "
                "LEFT JOIN Peluqueria p ON s.id_servicio = p.id_peluqueria "
                "LEFT JOIN Cirugia c ON s.id_servicio = c.id_cirugia;")
    datos = cur.fetchall()
    # Añadimos encabezados ficticios para mostrar en tabla
    cur.close()
    return jsonify([["ID", "Precio (Bs)","Nombre","Tipo Corte","Tipo Cirugia"]] + datos)

@app.route('/listar/personal')
def listar_personal():
    cur = conn.cursor()
    cur.execute("SELECT p.ci_personal, p.nombre, p.apellido_paterno, p.apellido_materno, v.especialidad, a.nivel, pe.tipo, ad.cargo FROM Personal p "
                "LEFT JOIN Veterinario v ON p.ci_personal = v.id_veterinario "
                "LEFT JOIN Asistente_Veterinario a ON p.ci_personal = a.id_asistente "
                "LEFT JOIN Peluquero pe ON p.ci_personal = pe.id_peluquero "
                "LEFT JOIN Personal_Administrativo ad ON p.ci_personal = ad.id_admin "
                "ORDER BY p.ci_personal ASC;")
    datos = cur.fetchall()
    cur.close()
    return jsonify([["CI", "Nombre","Ap Paterno","Ap Materno","Especialidad","Nivel Asistente","Tipo de Corte ","Cargo Admin"]] + datos)




@app.route('/agregar/propietario', methods=['POST'])
def agregar_propietario():
    data = request.json
    cursor.execute("""
        INSERT INTO Propietario (ci, nombre, apellido, direccion, telefono, correo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (data['ci'], data['nombre'], data['apellido'], data['direccion'], data['telefono'], data['correo']))
    conn.commit()
    return jsonify({'mensaje': 'Propietario agregado con éxito'})


@app.route('/agregar/mascota', methods=['POST'])
def agregar_mascota():
    data = request.json
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Mascota (edad, nombre, especie, raza, color, sexo, ci_propietario)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['edad'],
            data['nombre'],
            data['especie'],
            data['raza'],
            data['color'],
            data['sexo'],
            data['ci_propietario']
        ))
        conn.commit()
        cursor.close()
        return jsonify({'mensaje': 'Mascota agregada con éxito'})
    except Exception as e:
        conn.rollback()  # ← Esto es clave para limpiar la transacción
        return jsonify({'error': str(e)})



@app.route('/agregar/personal', methods=['POST'])
def agregar_personal():
    data = request.json
    cursor.execute("""
        INSERT INTO Personal (ci_personal, nombre, apellido_paterno, apellido_materno, turno)
        VALUES (%s, %s, %s, %s, %s)
    """, (data['ci_personal'], data['nombre'], data['apellido_paterno'], data['apellido_materno'], data['turno']))
    subtipo = data.get('rol')
    if subtipo == 'veterinario':
        cursor.execute("INSERT INTO Veterinario (id_veterinario,especialidad) VALUES (%s,%s)", (data['ci_personal'],data['especialidad'],))
    elif subtipo == 'asistente':
        cursor.execute("INSERT INTO Asistente_Veterinario (id_asistente,nivel) VALUES (%s,%s)", (data['ci_personal'],data['nivel'],))
    elif subtipo == 'administrativo':
        cursor.execute("INSERT INTO Veterinario (id_admin,cargo) VALUES (%s,%s)", (data['ci_personal'],data['tipo'],))
    elif subtipo == 'peluquero':
        cursor.execute("INSERT INTO Veterinario (id_peluquero,tipo) VALUES (%s,%s)", (data['ci_personal'],data['cargo'],))
    conn.commit()
    return jsonify({'mensaje': 'Personal agregado con éxito'})


@app.route('/agregar/servicio', methods=['POST'])
def agregar_servicio():
    data = request.json
    cursor.execute("""
        INSERT INTO Servicio (precio) VALUES (%s) RETURNING id_servicio
    """, (data['precio'],))
    id_servicio = cursor.fetchone()[0]

    subtipo = data.get('subtipo')
    if subtipo == 'vacunatorio':
        cursor.execute("""
            INSERT INTO Vacunatorio (id_vacuna, nombre, dosis, frecuencia)
            VALUES (%s, %s, %s, %s)
        """, (id_servicio, data['nombre'], data['dosis'], data['frecuencia']))
    elif subtipo == 'peluqueria':
        cursor.execute("""
            INSERT INTO Peluqueria (id_peluqueria, corte_unas, tipo_corte)
            VALUES (%s, %s, %s)
        """, (id_servicio, data['corte_unas'] == 'true', data['tipo_corte']))
    elif subtipo == 'cirugia':
        cursor.execute("""
            INSERT INTO Cirugia (id_cirugia, tipo, complejidad)
            VALUES (%s, %s, %s)
        """, (id_servicio, data['tipo'], data['complejidad']))

    conn.commit()
    return jsonify({'mensaje': 'Servicio agregado con éxito'})


@app.route('/ver_propietario', methods=['POST'])
def ver_propietario():
    data = request.get_json()
    ci = data.get('ci')

    try:
        cur = conn.cursor()
        cur.execute("SELECT obtener_propietario(%s)", (ci,))
        resultado = cur.fetchone()
        cur.close()

        if resultado and resultado[0]:
            return jsonify({'resultado': resultado[0]})
        else:
            return jsonify({'resultado': 'Propietario no encontrado.'})

    except Exception as e:
        conn.rollback()  # 👈 IMPORTANTE: limpia el error de la transacción
        return jsonify({'error': str(e)})


@app.route('/ver_mascota', methods=['POST'])
def ver_mascota():
    data = request.get_json()
    id_mascota = data.get('id_mascota')

    try:
        cur = conn.cursor()
        cur.execute("SELECT obtener_mascota(%s)", (id_mascota,))
        resultado = cur.fetchone()
        cur.close()

        if resultado and resultado[0]:
            return jsonify({'resultado': resultado[0]})
        else:
            return jsonify({'resultado': 'Mascota no encontrada.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})

@app.route('/ver_personal', methods=['POST'])
def ver_personal():
    data = request.get_json()
    ci = data.get('ci')

    try:
        cur = conn.cursor()
        cur.execute("SELECT obtener_personal(%s)", (ci,))
        resultado = cur.fetchone()
        cur.close()

        if resultado and resultado[0]:
            return jsonify({'resultado': resultado[0]})
        else:
            return jsonify({'resultado': 'Personal no encontrado.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})

@app.route('/ver_servicio', methods=['POST'])
def ver_servicio():
    data = request.get_json()
    id_servicio = data.get('id_servicio')

    try:
        cur = conn.cursor()
        cur.execute("SELECT obtener_servicio(%s)", (id_servicio,))
        resultado = cur.fetchone()
        cur.close()

        if resultado and resultado[0]:
            return jsonify({'resultado': resultado[0]})
        else:
            return jsonify({'resultado': 'Servicio no encontrado.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})


@app.route('/eliminar_propietario', methods=['POST'])
def eliminar_propietario():
    data = request.get_json()
    ci = data.get('ci')

    try:
        cur = conn.cursor()
        # Elimina de la tabla propietario
        cur.execute("DELETE FROM propietario WHERE ci = %s", (ci,))
        filas_afectadas = cur.rowcount
        conn.commit()
        cur.close()

        if filas_afectadas == 0:
            return jsonify({'success': False, 'message': 'No se encontró un propietario con ese CI.'})
        else:
            return jsonify({'success': True, 'message': 'Propietario eliminado correctamente.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/eliminar_mascota', methods=['POST'])
def eliminar_mascota():
    data = request.get_json()
    id_mascota = data.get('id_mascota')

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM mascota WHERE id_mascota = %s", (id_mascota,))
        filas_afectadas = cur.rowcount
        conn.commit()
        cur.close()

        if filas_afectadas == 0:
            return jsonify({'success': False, 'message': 'No se encontró una mascota con ese ID.'})
        else:
            return jsonify({'success': True, 'message': 'Mascota eliminada correctamente.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/eliminar_servicio', methods=['POST'])
def eliminar_servicio():
    data = request.get_json()
    id_servicio = data.get('id_servicio')

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM servicio WHERE id_servicio = %s", (id_servicio,))
        filas_afectadas = cur.rowcount
        conn.commit()
        cur.close()

        if filas_afectadas == 0:
            return jsonify({'success': False, 'message': 'No se encontró un servicio con ese ID.'})
        else:
            return jsonify({'success': True, 'message': 'Servicio eliminado correctamente.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/eliminar_personal', methods=['POST'])
def eliminar_personal():
    data = request.get_json()
    ci = data.get('ci')

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM personal WHERE ci_personal = %s", (ci,))
        filas_afectadas = cur.rowcount
        conn.commit()
        cur.close()

        if filas_afectadas == 0:
            return jsonify({'success': False, 'message': 'No se encontró personal con ese CI.'})
        else:
            return jsonify({'success': True, 'message': 'Personal eliminado correctamente.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)