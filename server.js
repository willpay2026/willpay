const { Client } = require('pg');
const express = require('express');
const path = require('path');
const ejs = require('ejs');
const app = express();

// CONFIGURACIÓN DE INTERFAZ
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// LA LLAVE DEL BÚNKER (POSTGRESQL)
const connectionString = 'postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?ssl=true';
const client = new Client({ connectionString });
client.connect()
    .then(() => console.log("--- CONECTADO A LA CAJA FUERTE DE POSTGRES ---"))
    .catch(err => console.error("Error de conexión:", err));

// CONFIGURACIÓN DE TABLAS
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

// --- RUTA DE LOGIN REAL ---
app.post('/acceso', async (req, res) => {
    const { usuario, password } = req.body; // Viene del formulario index.html
    try {
        const result = await client.query(
            'SELECT * FROM socios_oficiales WHERE telefono = $1 AND pin = $2', 
            [usuario, password]
        );

        if (result.rows.length > 0) {
            const user = result.rows[0];
            if (user.rol === 'ADMIN' || usuario === '04120000000') { // Pon aquí tu número de admin
                res.redirect('/ceo');
            } else {
                res.redirect('/boveda');
            }
        } else {
            res.send("<script>alert('Datos incorrectos'); window.location='/';</script>");
        }
    } catch (err) {
        res.status(500).send("Error en el búnker");
    }
});

// --- RUTA DEL CEO ---
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

// --- RUTA DE LA BÓVEDA (SOCIO) ---
app.get('/boveda', (req, res) => {
    const usuario = {
        nombre: "Socio Registrado",
        id_adn: "WP-ADN-321",
        saldo_disponible: 0.00,
        qr_data: "WILL-PAY-SOCIO"
    };
    res.render('boveda.html', { u: usuario, m: [] });
});

// ENCENDIDO EN PUERTO 10000 (PARA RENDER)
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log(`--- BORNKER VA A PAGAR: SISTEMA EN PUERTO ${PORT} ---`);
});
