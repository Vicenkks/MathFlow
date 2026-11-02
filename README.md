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

## API
- `GET /api/tasks` lista actividades.
- `POST /api/tasks` crea actividad `{ "title": "Integrales", "day": "2026-11-02", "time": "16:00" }`.
- `PATCH /api/tasks/:id` cambia estado `{ "done": true }`.
- `DELETE /api/tasks/:id` elimina actividad.
- `GET /api/integral/today?date=YYYY-MM-DD` devuelve ejercicio diario.
- `POST /api/integral/complete` registra resolución `{ "day": "YYYY-MM-DD" }`.
- `GET /api/stats` devuelve estadísticas.