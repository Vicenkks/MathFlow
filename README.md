# MathFlow

Aplicación web de rutinas, horarios e integral diaria.

## Requisitos
Node.js 20 o superior, npm.

## Iniciar
```bash
npm install
npm start
```
Abre http://localhost:3000

SQLite se crea automáticamente en `mathflow.db`. Para respaldar tus datos, detén el servidor y copia ese archivo.

## API
- `GET /api/tasks` lista actividades.
- `POST /api/tasks` crea actividad `{ "title": "Integrales", "day": "2026-11-02", "time": "16:00" }`.
- `PATCH /api/tasks/:id` cambia estado `{ "done": true }`.
- `DELETE /api/tasks/:id` elimina actividad.
- `GET /api/integral/today?date=YYYY-MM-DD` devuelve ejercicio diario.
- `POST /api/integral/complete` registra resolución `{ "day": "YYYY-MM-DD" }`.
- `GET /api/stats` devuelve estadísticas.

## Notas
- Los ejercicios rotan entre 10 integrales; amplía `exercises` en `server.js` para tener más variedad.
- La comprobación numérica en el navegador es orientativa, no una prueba simbólica completa. Las respuestas pueden diferir por una constante de integración.
- MathJax y math.js se cargan desde CDN y requieren internet. El servidor y SQLite funcionan localmente.
- La fecha diaria se envía desde el navegador para usar el día local. El registro de resolución usa actualmente la fecha UTC del servidor; cerca de medianoche local puede no coincidir. Ajusta la zona horaria del servidor si lo necesitas.
- Diseñado para uso personal local; antes de publicarlo se necesitan autenticación, límites de uso y validación más estricta.
