const { Client } = require('pg');
const express = require('express');
const path = require('path');
const ejs = require('ejs');
const app = express();

// 1. CONFIGURACIÓN DE INTERFAZ Y MOTORES
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// 2. CONEXIÓN A POSTGRESQL (LA LLAVE DEL BÚNKER)
const connectionString = 'postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?ssl=true';
const client = new Client({ connectionString });
client.connect()
    .then(() => console.log("--- CONECTADO A LA CAJA FUERTE DE POSTGRES ---"))
    .catch(err => console.error("Error de conexión:", err));

// 3. ASEGURAR QUE LA TABLA EXISTE
const setupDB = async () => {
    const query = `
        CREATE TABLE IF NOT EXISTS socios_oficiales (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            saldo DECIMAL(15,2) DEFAULT 0.00,
            rol TEXT DEFAULT 'SOCIO',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    `;
    await client.query(query);
    console.log("Tabla 'socios_oficiales' verificada.");
};
setupDB();

// --- 4. RUTAS DE NAVEGACIÓN ---

// A. PANTALLA DE CARGA (Splash con logonuevo.png)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// B. FORMULARIO DE ACCESO (Después de los 5 segundos)
app.get('/acceso', (req, res) => {
    res.render('login_form.html'); // Asegúrate de crear este archivo en /templates
});

// C. PROCESAR EL LOGIN REAL
app.post('/login_process', async (req, res) => {
    const { usuario, password } = req.body;
    try {
        const result = await client.query(
            'SELECT * FROM socios_oficiales WHERE telefono = $1 AND pin = $2', 
            [usuario, password]
        );

        if (result.rows.length > 0) {
            const user = result.rows[0];
            // Si eres tú o tiene rol ADMIN, vas al panel CEO
            if (user.rol === 'ADMIN' || usuario === '04120000000') {
                res.redirect('/ceo');
            } else {
                res.redirect('/boveda');
            }
        } else {
            res.send("<script>alert('Datos incorrectos o ADN no registrado'); window.location='/acceso';</script>");
        }
    } catch (err) {
        console.error(err);
        res.status(500).send("Error interno en el búnker");
    }
});

// D. RUTA DEL CEO (BÚNKER MASTER)
app.get('/ceo', (req, res) => {
    const u = { 
        id_dna: "CEO-0001-FOUNDER",
        nombre: "WILFREDO DONQUIZ", 
        saldo_bs: 0.00,
        ultimo_id_pendiente: "000000",
        ultimo_monto_pendiente: 0.00
    };
    res.render('ceo_panel.html', { u: u, m: [] });
});

// E. RUTA DE LA BÓVEDA (VISTA DEL SOCIO)
app.get('/boveda', (req, res) => {
    const usuario = {
        nombre: "Socio Registrado",
        id_adn: "WP-ADN-321",
        saldo_disponible: 0.00,
        qr_data: "WILL-PAY-SOCIO"
    };
    res.render('boveda.html', { u: usuario, m: [] });
});

// 5. ENCENDIDO EN PUERTO 10000
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log(`--- BORNKER VA A PAGAR: SISTEMA EN PUERTO ${PORT} ---`);
});
