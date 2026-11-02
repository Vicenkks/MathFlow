import express from 'express';
import Database from 'better-sqlite3';
import {fileURLToPath} from 'url';
import path from 'path';
const root=path.dirname(fileURLToPath(import.meta.url));
const app=express();const db=new Database(path.join(root,'mathflow.db'));
db.pragma('journal_mode = WAL');
db.exec(`CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT NOT NULL, day TEXT NOT NULL, time TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0);CREATE TABLE IF NOT EXISTS solutions(day TEXT PRIMARY KEY, completed INTEGER NOT NULL DEFAULT 1);`);
app.use(express.json({limit:'10kb'}));app.use(express.static(path.join(root,'public')));
const exercises=[
{q:'\\int 2x\\,dx',answer:'x^2+C',hint:'Regla de la potencia',latex:'2*x'},
{q:'\\int 3x^2\\,dx',answer:'x^3+C',hint:'Aumenta el exponente en uno',latex:'3*x^2'},
{q:'\\int \\cos(x)\\,dx',answer:'\\sin(x)+C',hint:'Derivada de seno',latex:'cos(x)'},
{q:'\\int \\frac{1}{x}\\,dx',answer:'\\ln|x|+C',hint:'Piensa en logaritmos',latex:'1/x'},
{q:'\\int e^x\\,dx',answer:'e^x+C',hint:'La exponencial se conserva',latex:'exp(x)'},
{q:'\\int 4x^3\\,dx',answer:'x^4+C',hint:'Regla de la potencia',latex:'4*x^3'},
{q:'\\int \\sin(x)\\,dx',answer:'-\\cos(x)+C',hint:'Derivada de coseno',latex:'sin(x)'},
{q:'\\int \\frac{1}{1+x^2}\\,dx',answer:'\\arctan(x)+C',hint:'Derivada de arctangente',latex:'1/(1+x^2)'},
{q:'\\int 6x\\,dx',answer:'3x^2+C',hint:'Integra término a término',latex:'6*x'},
{q:'\\int 2e^{2x}\\,dx',answer:'e^{2x}+C',hint:'Regla de la cadena inversa',latex:'2*exp(2*x)'}
];
const dateOk=s=>/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s+'T00:00:00Z'));
const today=(req)=>{const d=req.query.date;return typeof d==='string'&&dateOk(d)?d:new Date().toISOString().slice(0,10)};
const exerciseFor=d=>exercises[Math.floor(Date.parse(d+'T00:00:00Z')/86400000)%exercises.length];
app.get('/api/tasks',(req,res)=>res.json(db.prepare('SELECT * FROM tasks ORDER BY day,time,id').all()));
app.post('/api/tasks',(req,res)=>{const {title,day,time}=req.body||{};if(typeof title!=='string'||!title.trim()||title.length>120||!dateOk(day)||!/^([01]\d|2[0-3]):[0-5]\d$/.test(time||''))return res.status(400).json({error:'Datos inválidos'});const info=db.prepare('INSERT INTO tasks(title,day,time) VALUES(?,?,?)').run(title.trim(),day,time);res.status(201).json(db.prepare('SELECT * FROM tasks WHERE id=?').get(info.lastInsertRowid));});
app.patch('/api/tasks/:id',(req,res)=>{if(!Number.isSafeInteger(Number(req.params.id))||typeof req.body?.done!=='boolean')return res.status(400).json({error:'Datos inválidos'});const r=db.prepare('UPDATE tasks SET done=? WHERE id=?').run(Number(req.body.done),Number(req.params.id));if(!r.changes)return res.sendStatus(404);res.json({ok:true});});
app.delete('/api/tasks/:id',(req,res)=>{const r=db.prepare('DELETE FROM tasks WHERE id=?').run(Number(req.params.id));res.status(r.changes?204:404).end();});
app.get('/api/integral/today',(req,res)=>{const day=today(req);const {q,hint}=exerciseFor(day);res.json({day,q,hint,completed:!!db.prepare('SELECT 1 FROM solutions WHERE day=?').get(day)});});
app.post('/api/integral/complete',(req,res)=>{const {day}=req.body||{};if(!dateOk(day)||day!==new Date().toISOString().slice(0,10))return res.status(400).json({error:'Fecha inválida'});db.prepare('INSERT OR IGNORE INTO solutions(day) VALUES(?)').run(day);res.json({ok:true});});
app.get('/api/stats',(req,res)=>res.json({tasks:db.prepare('SELECT COUNT(*) n FROM tasks').get().n,done:db.prepare('SELECT COUNT(*) n FROM tasks WHERE done=1').get().n,integrals:db.prepare('SELECT COUNT(*) n FROM solutions').get().n}));
app.listen(3000,()=>console.log('MathFlow: http://localhost:3000'));
