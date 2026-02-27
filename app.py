@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    # 1. Capturamos los datos del formulario KYC
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea', 'N/A') # Si no aplica, pone N/A
    
    # 2. Manejo de la Foto de Cédula
    foto = request.files.get('foto_cedula')
    nombre_archivo = "sin_foto.jpg"
    if foto:
        nombre_archivo = f"cedula_{cedula}.jpg"
        # Aquí se guardaría en una carpeta 'uploads' (necesitas crearla en GitHub)
        foto.save(os.path.join('static/uploads', nombre_archivo))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3. Verificamos si es el fundador para darle su bono de CEO
        saldo_inicial = 5000.00 if "Wilfredo" in nombre else 10.00
        rol = "CEO-FOUNDER" if "Wilfredo" in nombre else "USUARIO"

        # 4. Guardamos en la base de datos willpay_db
        cur.execute("""
            INSERT INTO usuarios (id, nombre, telefono, actividad, nombre_linea, foto_cedula, saldo, rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cedula, nombre, telefono, actividad, nombre_linea, nombre_archivo, saldo_inicial, rol))
        
        conn.commit()
        return render_template('ticket_bienvenida.html', nombre=nombre, id=cedula, saldo=saldo_inicial)

    except Exception as e:
        conn.rollback()
        return f"Error al registrar el legado: {e}", 500
    finally:
        cur.close()
        conn.close()
