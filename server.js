const { Client } = require('pg');
const express = require('express');
const path = require('path');
const ejs = require('ejs');
const app = express();

// 1. CONFIGURACIÓN DE INTERFAZ
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// 2. CONEXIÓN A POSTGRES (LLAVE DEL BÚNKER)
const connectionString = 'postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?ssl=true';
const client = new Client({ connectionString });
client.connect().catch(err => console.error("Error de conexión:", err));

// 3. RUTAS DE NAVEGACIÓN
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'static', 'index.html')));
app.get('/acceso', (req, res) => res.render('acceso.html'));
app.get('/registro', (req, res) => res.render('registro.html'));

// 4. MOTOR DE REGISTRO KYC
app.post('/procesar_registro', async (req, res) => {
    const { nombre, cedula, telefono, actividad, pin } = req.body;
    try {
        const query = `INSERT INTO socios_oficiales (nombre, telefono, pin, saldo, rol) 
                       VALUES ($1, $2, $3, 0.00, 'SOCIO') RETURNING *`;
        const result = await client.query(query, [nombre, telefono, pin]);
        res.render('ticket_bienvenida.html', { u: result.rows[0] });
    } catch (err) {
        res.send("<script>alert('Error: Datos ya registrados'); window.location='/registro';</script>");
    }
});

// 5. MOTOR DE PAGOS Y COMISIÓN (TU GANANCIA)
app.post('/procesar_pago_bs', async (req, res) => {
    const { monto, destino_id, emisor_id } = req.body;
    try {
        await client.query('BEGIN');
        const montoNum = parseFloat(monto);
        const comision = montoNum * 0.015; // TU 1.5%
        const total = montoNum + comision;

        await client.query('UPDATE socios_oficiales SET saldo = saldo - $1 WHERE id = $2', [total, emisor_id]);
        await client.query('UPDATE socios_oficiales SET saldo = saldo + $1 WHERE id = $2', [montoNum, destino_id]);
        await client.query("UPDATE socios_oficiales SET saldo = saldo + $1 WHERE rol = 'ADMIN'", [comision]);

        const op = await client.query('INSERT INTO pagos (emisor_id, receptor_id, monto, comision) VALUES ($1,$2,$3,$4) RETURNING id', 
        [emisor_id, destino_id, montoNum, comision]);
        
        await client.query('COMMIT');
        res.json({ status: 'Éxito', id_op: op.rows[0].id });
    } catch (e) {
        await client.query('ROLLBACK');
        res.status(500).json({ status: 'Error' });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`BÚNKER ONLINE EN PUERTO ${PORT}`));
