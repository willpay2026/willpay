import os
import datetime
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        rv = (cur.fetchone() if one else cur.fetchall()) if not commit else None
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error DB: {e}")
        return None

@app.route('/')
def index():
    return render_template('dashboard.html', user=None)

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=u)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
