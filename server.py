#!/usr/bin/env python3
"""MathFlow — web app + SQLite + API REST, usando solo Python estándar."""

from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import json
import re
import sqlite3
import sys

BASE = Path(__file__).resolve().parent
DB = BASE / 'data' / 'mathflow.sqlite3'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LEVELS = {'basico', 'intermedio', 'avanzado'}
CATEGORIES = {'Cálculo', 'Álgebra', 'Geometría', 'Repaso', 'Descanso', 'Otro'}

# Cada entrada: expresión, pista, resultado, explicación. Las respuestas incluyen + C.
CHALLENGES = {
    'basico': [
        ('∫ 6x² dx', 'Aplica la regla de la potencia: suma 1 al exponente y divide.', '2x³ + C', 'Como la derivada de 2x³ es 6x², esa es una primitiva.'),
        ('∫ (4x + 3) dx', 'Integra cada término por separado.', '2x² + 3x + C', '∫4x dx = 2x²; ∫3 dx = 3x.'),
        ('∫ 5eˣ dx', 'La derivada de eˣ es eˣ.', '5eˣ + C', 'El factor constante 5 se conserva.'),
        ('∫ 3cos(x) dx', '¿Qué función tiene cos(x) como derivada?', '3sin(x) + C', 'La derivada de sin(x) es cos(x).'),
        ('∫ 7x⁶ dx', 'Usa ∫xⁿ dx = xⁿ⁺¹/(n+1), con n ≠ −1.', 'x⁷ + C', '7x⁶ es la derivada de x⁷.'),
        ('∫ (8x³ − 2x) dx', 'Puedes integrar la resta término a término.', '2x⁴ − x² + C', '8x³ pasa a 2x⁴ y −2x pasa a −x².'),
        ('∫ 4sin(x) dx', 'Recuerda que la derivada de cos(x) tiene un signo menos.', '−4cos(x) + C', 'La derivada de −cos(x) es sin(x).'),
        ('∫ 9 dx', 'La integral de una constante k es kx.', '9x + C', 'La derivada de 9x es 9.'),
        ('∫ (3x² + 2x − 4) dx', 'Integra cada término del polinomio.', 'x³ + x² − 4x + C', 'Los tres términos se integran con la regla de la potencia.'),
        ('∫ 1/x dx', 'Este es el caso especial n = −1.', 'ln|x| + C', 'La derivada de ln|x| es 1/x, para x ≠ 0.'),
        ('∫ 10x⁴ dx', 'Suma uno al exponente y divide entre cinco.', '2x⁵ + C', 'd(2x⁵)/dx = 10x⁴.'),
        ('∫ 2eˣ dx', 'La exponencial eˣ se conserva al integrar.', '2eˣ + C', 'La constante multiplicativa 2 permanece.'),
        ('∫ (6x⁵ + 12x²) dx', 'Aplica la regla de potencia a cada sumando.', 'x⁶ + 4x³ + C', 'La derivada de x⁶ + 4x³ recupera el integrando.'),
        ('∫ 5/x dx', 'Usa el logaritmo natural y el valor absoluto.', '5ln|x| + C', 'La derivada de 5ln|x| es 5/x.'),
        ('∫ (2cos(x) − 3sin(x)) dx', 'Integra el seno y el coseno cuidando los signos.', '2sin(x) + 3cos(x) + C', 'd(sin x)/dx = cos x, y d(cos x)/dx = −sin x.'),
        ('∫ (x² + 4x + 1) dx', 'Integra los tres sumandos.', 'x³/3 + 2x² + x + C', 'La derivada de cada término devuelve el polinomio.'),
        ('∫ sec²(x) dx', 'Recuerda la derivada de tan(x).', 'tan(x) + C', 'd(tan x)/dx = sec²(x).'),
        ('∫ (12x³ − 6x²) dx', 'Usa la regla de la potencia dos veces.', '3x⁴ − 2x³ + C', 'd(3x⁴ − 2x³)/dx = 12x³ − 6x².'),
    ],
    'intermedio': [
        ('∫ 2x(x² + 5)³ dx', 'Prueba u = x² + 5; entonces du = 2x dx.', '(x² + 5)⁴/4 + C', 'Con u = x² + 5 queda ∫u³ du = u⁴/4.'),
        ('∫ 3e³ˣ dx', 'Usa sustitución u = 3x.', 'e³ˣ + C', 'd(e³ˣ)/dx = 3e³ˣ.'),
        ('∫ 2x/(x² + 1) dx', 'El numerador es la derivada del denominador.', 'ln(x² + 1) + C', 'Con u = x² + 1, la integral es ∫du/u.'),
        ('∫ 4cos(4x) dx', 'Usa la regla de la cadena en sentido inverso.', 'sin(4x) + C', 'La derivada de sin(4x) es 4cos(4x).'),
        ('∫ 6x(3x² + 2)⁴ dx', 'Prueba u = 3x² + 2.', '(3x² + 2)⁵/5 + C', 'du = 6x dx, así que queda ∫u⁴ du.'),
        ('∫ 5/(5x + 7) dx', 'Usa u = 5x + 7 y recuerda ln|u|.', 'ln|5x + 7| + C', 'La derivada del denominador es 5, justo el numerador.'),
        ('∫ 2sin(2x) dx', 'Al derivar cos(2x), aparece un factor 2.', '−cos(2x) + C', 'La derivada de −cos(2x) es 2sin(2x).'),
        ('∫ 4x/(2x² + 9) dx', 'El numerador es la derivada del denominador.', 'ln(2x² + 9) + C', 'u = 2x² + 9, du = 4x dx.'),
        ('∫ 3/(1 + 9x²) dx', 'Recuerda que d(arctan u)/dx = u′/(1 + u²).', 'arctan(3x) + C', 'Al derivar arctan(3x) sale 3/(1 + 9x²).'),
        ('∫ (2x + 3)⁴ dx', 'Usa u = 2x + 3, du = 2dx.', '(2x + 3)⁵/10 + C', '∫u⁴ du/2 = u⁵/10.'),
        ('∫ e⁻²ˣ dx', 'Al integrar eᵃˣ divide entre a.', '−e⁻²ˣ/2 + C', 'La derivada de −e⁻²ˣ/2 devuelve e⁻²ˣ.'),
        ('∫ x/√(x² + 4) dx', 'Elige u = x² + 4.', '√(x² + 4) + C', 'du = 2x dx y ∫u⁻¹ᐟ² du/2 = √u.'),
        ('∫ 2x cos(x²) dx', 'Usa u = x².', 'sin(x²) + C', 'du = 2x dx, luego ∫cos(u)du = sin(u).'),
        ('∫ 6x/(3x² + 4) dx', 'Sustituye el denominador.', 'ln(3x² + 4) + C', 'u = 3x² + 4 y du = 6x dx.'),
        ('∫ (3x + 1)² dx', 'Sustitución lineal u = 3x + 1.', '(3x + 1)³/9 + C', '∫u² du/3 = u³/9.'),
        ('∫ 5sin(5x) dx', 'Identifica la derivada de cos(5x).', '−cos(5x) + C', 'La derivada de −cos(5x) es 5sin(5x).'),
        ('∫ 2x eˣ² dx', 'Sustituye u = x².', 'eˣ² + C', 'La derivada de e^(x²) es 2x e^(x²).'),
        ('∫ 1/(x + 4) dx', 'La primitiva de 1/u es ln|u|.', 'ln|x + 4| + C', 'La derivada de ln|x + 4| es 1/(x + 4).'),
    ],
    'avanzado': [
        ('∫ x eˣ dx', 'Prueba integración por partes: u = x, dv = eˣ dx.', '(x − 1)eˣ + C', 'Por partes: xeˣ − ∫eˣdx = (x − 1)eˣ.'),
        ('∫ x sin(x) dx', 'Por partes: u = x, dv = sin(x)dx.', '−x cos(x) + sin(x) + C', 'Integra v = −cos(x) y aplica ∫u dv = uv − ∫v du.'),
        ('∫ ln(x) dx', 'Por partes: u = ln(x), dv = dx. Considera x > 0.', 'x ln(x) − x + C', 'xln(x) − ∫x·(1/x)dx = xln(x) − x.'),
        ('∫ x cos(x) dx', 'Por partes: u = x y dv = cos(x)dx.', 'x sin(x) + cos(x) + C', 'xsin(x) − ∫sin(x)dx = xsin(x) + cos(x).'),
        ('∫ x²eˣ dx', 'Aplica integración por partes dos veces.', 'eˣ(x² − 2x + 2) + C', 'Primero x²eˣ − 2∫xeˣdx y luego integra xeˣ por partes.'),
        ('∫ x ln(x) dx', 'Por partes: u = ln(x), dv = xdx; x > 0.', '(x²/2)ln(x) − x²/4 + C', 'Por partes resulta x²ln(x)/2 − (1/2)∫x dx.'),
        ('∫ eˣ sin(x) dx', 'Aplica partes dos veces y despeja la integral original.', 'eˣ(sin(x) − cos(x))/2 + C', 'Tras dos integraciones por partes, aparecen 2I = eˣ(sin x − cos x).'),
        ('∫ eˣ cos(x) dx', 'Partes dos veces: la integral original reaparece.', 'eˣ(sin(x) + cos(x))/2 + C', 'Al despejar se obtiene 2I = eˣ(sin x + cos x).'),
        ('∫ arctan(x) dx', 'Integra por partes con u = arctan(x).', 'x arctan(x) − ln(1 + x²)/2 + C', 'Por partes: xarctan(x) − ∫x/(1 + x²)dx.'),
        ('∫ 1/(x² + 9) dx', 'Usa la forma ∫1/(x² + a²)dx.', 'arctan(x/3)/3 + C', 'Con a = 3, la integral es (1/3)arctan(x/3).'),
        ('∫ tan(x) dx', 'Escribe tan(x) = sin(x)/cos(x).', '−ln|cos(x)| + C', 'Sustituye u = cos(x), du = −sin(x)dx.'),
        ('∫ sin²(x) dx', 'Usa sin²(x) = (1 − cos(2x))/2.', 'x/2 − sin(2x)/4 + C', 'Integra los dos términos tras la identidad del ángulo doble.'),
        ('∫ cos²(x) dx', 'Usa cos²(x) = (1 + cos(2x))/2.', 'x/2 + sin(2x)/4 + C', 'La identidad de ángulo doble simplifica el integrando.'),
        ('∫ 1/(x ln(x)) dx', 'Sustituye u = ln(x), en x > 0 y x ≠ 1.', 'ln|ln(x)| + C', 'du = dx/x, luego ∫du/u = ln|u|.'),
        ('∫ sec(x)tan(x) dx', 'Recuerda la derivada de sec(x).', 'sec(x) + C', 'd(sec(x))/dx = sec(x)tan(x).'),
        ('∫ x/(x² + 4) dx', 'Una sustitución produce un logaritmo.', 'ln(x² + 4)/2 + C', 'u = x² + 4, du = 2x dx.'),
        ('∫ x e²ˣ dx', 'Por partes: u = x, dv = e²ˣ dx.', 'e²ˣ(2x − 1)/4 + C', 'x·e²ˣ/2 − ∫e²ˣ/2 dx = e²ˣ(2x−1)/4.'),
        ('∫ x³ln(x) dx', 'Por partes: u = ln(x), dv = x³ dx, x > 0.', '(x⁴/4)ln(x) − x⁴/16 + C', 'Por partes: (x⁴/4)ln(x) − (1/4)∫x³ dx.'),
    ],
}


def db_connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 10000')
    return conn


def init_db():
    with db_connect() as conn:
        conn.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS routines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                days TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS completions (
                routine_id INTEGER NOT NULL REFERENCES routines(id) ON DELETE CASCADE,
                day TEXT NOT NULL,
                PRIMARY KEY (routine_id, day)
            );
            CREATE TABLE IF NOT EXISTS challenge_progress (
                day TEXT NOT NULL,
                level TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (day, level)
            );
            CREATE TABLE IF NOT EXISTS notes (
                day TEXT PRIMARY KEY,
                content TEXT NOT NULL DEFAULT ''
            );
        ''')


def check_day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Fecha inválida. Usa AAAA-MM-DD.')
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Fecha del calendario inválida.') from exc
    return value


def check_routine(payload):
    if not isinstance(payload, dict):
        raise ValueError('El cuerpo debe ser un objeto JSON.')
    title = payload.get('title')
    category = payload.get('category')
    time = payload.get('time')
    duration = payload.get('duration')
    days = payload.get('days')
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 90:
        raise ValueError('El nombre debe tener entre 1 y 90 caracteres.')
    if category not in CATEGORIES:
        raise ValueError('Categoría inválida.')
    if not isinstance(time, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', time):
        raise ValueError('La hora debe tener formato HH:MM (24 horas).')
    if type(duration) is not int or not 5 <= duration <= 480:
        raise ValueError('La duración debe estar entre 5 y 480 minutos.')
    if not isinstance(days, list) or not days or any(type(x) is not int or x not in range(7) for x in days):
        raise ValueError('Selecciona al menos un día válido de la semana.')
    return (title.strip(), category, time, duration, json.dumps(sorted(set(days))))


def serialize_routine(row):
    data = dict(row)
    data['days'] = json.loads(data['days'])
    data.pop('created_at', None)
    return data


class Handler(BaseHTTPRequestHandler):
    def json_response(self, code, payload):
        content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def get_body(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > 64000:
            raise ValueError('El JSON debe existir y pesar menos de 64 KB.')
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('JSON inválido.') from exc

    def dispatch(self, method):
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        today = date.today().isoformat()
        day = check_day(query.get('date', [today])[0])

        if method == 'GET' and path in ('/', '/index.html', '/styles.css', '/app.js', '/favicon.svg'):
            file_name = 'index.html' if path == '/' else path[1:]
            file = BASE / file_name
            if not file.is_file():
                return self.json_response(404, {'error': 'Archivo no encontrado.'})
            mime = {'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.svg': 'image/svg+xml'}[file.suffix]
            content = file.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
            return

        if method == 'GET' and path == '/api/health':
            return self.json_response(200, {'ok': True, 'database': 'SQLite', 'challenge': 'Integral diaria'})

        if path == '/api/routines':
            if method == 'GET':
                with db_connect() as conn:
                    rows = conn.execute('SELECT * FROM routines ORDER BY time ASC, id ASC').fetchall()
                return self.json_response(200, {'routines': [serialize_routine(x) for x in rows]})
            if method == 'POST':
                args = check_routine(self.get_body())
                with db_connect() as conn:
                    cur = conn.execute('INSERT INTO routines(title,category,time,duration,days) VALUES(?,?,?,?,?)', args)
                    row = conn.execute('SELECT * FROM routines WHERE id=?', (cur.lastrowid,)).fetchone()
                return self.json_response(201, {'routine': serialize_routine(row)})

        match = re.fullmatch(r'/api/routines/(\d+)', path)
        if match:
            routine_id = int(match.group(1))
            if method == 'PUT':
                args = check_routine(self.get_body())
                with db_connect() as conn:
                    cur = conn.execute('UPDATE routines SET title=?,category=?,time=?,duration=?,days=? WHERE id=?', (*args, routine_id))
                    if not cur.rowcount:
                        return self.json_response(404, {'error': 'Rutina no encontrada.'})
                    row = conn.execute('SELECT * FROM routines WHERE id=?', (routine_id,)).fetchone()
                return self.json_response(200, {'routine': serialize_routine(row)})
            if method == 'DELETE':
                with db_connect() as conn:
                    cur = conn.execute('DELETE FROM routines WHERE id=?', (routine_id,))
                return self.json_response(200 if cur.rowcount else 404, {'ok': bool(cur.rowcount)})

        if path == '/api/completions':
            if method == 'GET':
                start = check_day(query.get('start', [day])[0])
                end = check_day(query.get('end', [day])[0])
                if end < start:
                    raise ValueError('El fin debe ser posterior o igual al inicio.')
                with db_connect() as conn:
                    rows = conn.execute('SELECT routine_id, day FROM completions WHERE day BETWEEN ? AND ?', (start, end)).fetchall()
                return self.json_response(200, {'completions': [dict(x) for x in rows]})
            if method == 'PUT':
                payload = self.get_body()
                day_value = check_day(payload.get('date'))
                routine_id = payload.get('routine_id')
                completed = payload.get('completed')
                if type(routine_id) is not int or routine_id < 1 or type(completed) is not bool:
                    raise ValueError('Se requieren routine_id y completed (booleano).')
                with db_connect() as conn:
                    if not conn.execute('SELECT 1 FROM routines WHERE id=?', (routine_id,)).fetchone():
                        return self.json_response(404, {'error': 'Rutina no encontrada.'})
                    if completed:
                        conn.execute('INSERT OR IGNORE INTO completions(routine_id, day) VALUES(?,?)', (routine_id, day_value))
                    else:
                        conn.execute('DELETE FROM completions WHERE routine_id=? AND day=?', (routine_id, day_value))
                return self.json_response(200, {'ok': True})

        if path == '/api/challenge' and method == 'GET':
            level = query.get('level', ['intermedio'])[0]
            if level not in LEVELS:
                raise ValueError('Nivel de integral inválido.')
            day_value = check_day(query.get('date', [today])[0])
            bank = CHALLENGES[level]
            offset = {'basico': 0, 'intermedio': 5, 'avanzado': 11}[level]
            problem = bank[(date.fromisoformat(day_value).toordinal() + offset) % len(bank)]
            with db_connect() as conn:
                done = conn.execute('SELECT 1 FROM challenge_progress WHERE day=? AND level=?', (day_value, level)).fetchone()
            return self.json_response(200, {
                'date': day_value, 'level': level, 'expression': problem[0], 'hint': problem[1],
                'solution': problem[2], 'explanation': problem[3], 'completed': bool(done),
                'number': date.fromisoformat(day_value).toordinal(),
            })

        if path == '/api/challenge/complete' and method == 'PUT':
            payload = self.get_body()
            day_value = check_day(payload.get('date'))
            level = payload.get('level')
            completed = payload.get('completed')
            if level not in LEVELS or type(completed) is not bool:
                raise ValueError('Se requieren level válido y completed (booleano).')
            with db_connect() as conn:
                if completed:
                    conn.execute('INSERT OR IGNORE INTO challenge_progress(day,level) VALUES(?,?)', (day_value, level))
                else:
                    conn.execute('DELETE FROM challenge_progress WHERE day=? AND level=?', (day_value, level))
            return self.json_response(200, {'ok': True})

        if path == '/api/challenge/history' and method == 'GET':
            start = check_day(query.get('start', [day])[0])
            end = check_day(query.get('end', [day])[0])
            if end < start:
                raise ValueError('Intervalo inválido.')
            with db_connect() as conn:
                rows = conn.execute('SELECT day,level FROM challenge_progress WHERE day BETWEEN ? AND ?', (start,end)).fetchall()
            return self.json_response(200, {'completed': [dict(x) for x in rows]})

        if path == '/api/notes':
            day_value = check_day(query.get('date', [today])[0])
            if method == 'GET':
                with db_connect() as conn:
                    row = conn.execute('SELECT content FROM notes WHERE day=?', (day_value,)).fetchone()
                return self.json_response(200, {'date': day_value, 'content': row['content'] if row else ''})
            if method == 'PUT':
                payload = self.get_body()
                content = payload.get('content')
                if not isinstance(content, str) or len(content) > 10000:
                    raise ValueError('La nota debe tener como máximo 10.000 caracteres.')
                with db_connect() as conn:
                    conn.execute('INSERT INTO notes(day,content) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET content=excluded.content', (day_value, content))
                return self.json_response(200, {'ok': True})

        self.json_response(404, {'error': 'Ruta de API no encontrada.'})

    def do_GET(self):
        self.safe_dispatch('GET')

    def do_POST(self):
        self.safe_dispatch('POST')

    def do_PUT(self):
        self.safe_dispatch('PUT')

    def do_DELETE(self):
        self.safe_dispatch('DELETE')

    def safe_dispatch(self, method):
        try:
            self.dispatch(method)
        except ValueError as exc:
            self.json_response(400, {'error': str(exc)})
        except (sqlite3.Error, OSError) as exc:
            print('Error interno:', exc, file=sys.stderr)
            self.json_response(500, {'error': 'Error interno del servidor.'})


def main():
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'MathFlow listo: http://localhost:{PORT}')
    print(f'Base de datos: {DB}')
    print('Ctrl+C para detener.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
