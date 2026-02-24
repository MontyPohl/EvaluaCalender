# ⚡ EvaluaCalender

**Plataforma profesional de gestión de evaluaciones por challenges.**

---

## 📋 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+, Flask 3, SQLAlchemy |
| Base de datos | PostgreSQL |
| Autenticación | Flask-Login + bcrypt |
| Correo | Flask-Mail / SMTP |
| Scheduler | APScheduler (cancelación auto + recordatorios) |
| Frontend | HTML + CSS personalizado + JavaScript vanilla |
| Seguridad | CSRF (Flask-WTF), validación backend, hash bcrypt |

---

## 🏗 Estructura del proyecto

```
evaluacalender/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/
│   │   ├── user.py          # Modelo User (ADMIN/SUPERVISOR)
│   │   ├── challenge.py     # Modelo Challenge
│   │   ├── disponibilidad.py # Bloques horarios
│   │   └── evaluacion.py    # Evaluaciones/solicitudes
│   ├── routes/
│   │   ├── auth.py          # Login, registro, logout
│   │   ├── public.py        # Home, perfil supervisor, agendamiento
│   │   ├── supervisor.py    # Panel supervisor
│   │   └── admin.py         # Panel administrador
│   ├── services/
│   │   ├── email_service.py # Correos transaccionales
│   │   ├── scheduler.py     # Tareas automáticas APScheduler
│   │   └── availability_service.py # Lógica de disponibilidad
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── public/
│   │   ├── supervisor/
│   │   ├── admin/
│   │   └── errors/
│   └── static/
├── config/
│   └── settings.py          # Configuración centralizada
├── .env.example             # Plantilla de variables de entorno
├── create_db.py             # Script de inicialización de BD
├── requirements.txt
└── run.py                   # Punto de entrada
```

---

## 🚀 Instalación y puesta en marcha

### 1. Requisitos previos

- Python 3.11+
- PostgreSQL 14+
- Git (opcional)

### 2. Clonar y preparar el entorno

```bash
# Clonar el repositorio
git clone <url> evaluacalender
cd evaluacalender

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate.bat     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores reales
```

Variables clave en `.env`:

```env
SECRET_KEY=tu-clave-secreta-segura
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/evaluacalender
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu@gmail.com
MAIL_PASSWORD=tu-app-password
BASE_URL=https://tudominio.com
```

### 4. Crear la base de datos

```bash
# En PostgreSQL
psql -U postgres -c "CREATE DATABASE evaluacalender;"

# Crear tablas e insertar datos iniciales
python create_db.py
```

### 5. Ejecutar en desarrollo

```bash
python run.py
```

Accede a → **http://localhost:5000**

**Credenciales de admin por defecto:**
- Email: `admin@evaluacalender.com`
- Contraseña: `Admin1234!`
- ⚠️ **Cambia la contraseña inmediatamente en producción**

---

## 🌐 Despliegue en producción

### Con Gunicorn + Nginx

```bash
pip install gunicorn

# Iniciar Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

**Nginx config básica:**

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /ruta/a/evaluacalender/app/static;
        expires 30d;
    }
}
```

### Variables de entorno en producción

```env
FLASK_ENV=production
SECRET_KEY=<clave-aleatoria-larga-y-segura>
DATABASE_URL=postgresql://...
```

---

## 👥 Roles y funcionalidades

### ADMIN
- ✅ Crear/editar challenges
- ✅ Activar/desactivar challenges
- ✅ Ver todos los supervisores
- ✅ Desactivar/restaurar supervisores
- ✅ Vista global de evaluaciones con filtros

### SUPERVISOR
- ✅ Registro e inicio de sesión
- ✅ Definir disponibilidad mensual (bloques de 1 hora)
- ✅ Ver solicitudes pendientes con countdown de expiración
- ✅ Confirmar o rechazar evaluaciones
- ✅ Historial de evaluaciones

### Usuarios externos (sin cuenta)
- ✅ Ver supervisores disponibles
- ✅ Ver calendario mensual del supervisor
- ✅ Agendar evaluación (nombre, email, teléfono + challenge + horario)

---

## ⚙️ Reglas de negocio

| Regla | Detalle |
|-------|---------|
| Duración | Exactamente 1 hora por evaluación |
| Unicidad | Un solo supervisor por slot horario |
| Expiracion | PENDIENTE → CANCELADO_AUTO a las 12 horas |
| Liberación | Slot se libera al rechazar o cancelar |
| Recordatorio | Email 60 min antes a supervisor y evaluado |
| Sin cuenta | Usuarios externos no necesitan registrarse |

---

## 📧 Correos automáticos

| Evento | Destinatario |
|--------|-------------|
| Solicitud creada | Solicitante + Supervisor |
| Evaluación confirmada | Solicitante |
| Evaluación rechazada | Solicitante |
| Cancelación automática (12h) | Solicitante |
| Recordatorio 1h antes | Solicitante + Supervisor |

---

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con bcrypt (salt automático)
- ✅ Protección CSRF en todos los formularios (Flask-WTF)
- ✅ Validación backend obligatoria (no se confía en frontend)
- ✅ Verificación de disponibilidad antes de crear evaluación
- ✅ Control de roles (403 si accede con rol incorrecto)
- ✅ Soft delete de supervisores (no elimina datos históricos)

---

## 📦 requirements.txt

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Mail==0.10.0
Flask-Migrate==4.0.7
bcrypt==4.1.3
psycopg2-binary==2.9.9
APScheduler==3.10.4
python-dotenv==1.0.1
WTForms==3.1.2
SQLAlchemy==2.0.30
Werkzeug==3.0.3
pytz==2024.1
```

---

## 🛠 Comandos útiles

```bash
# Shell interactivo con contexto de la app
flask shell

# Ver logs en tiempo real (con Gunicorn)
gunicorn --log-level debug -w 1 "run:app"

# Crear migraciones (si usas Flask-Migrate)
flask db init
flask db migrate -m "initial"
flask db upgrade
```

---

## 📈 Escalabilidad

El sistema está preparado para:
- **20+ supervisores activos** concurrentes
- Pool de conexiones PostgreSQL configurado (`pool_pre_ping`, `pool_recycle`)
- Scheduler APScheduler en background thread (compatible con Gunicorn multi-worker con precaución)
- Para mayor escala: considera Celery + Redis en lugar de APScheduler

---

*EvaluaCalender · Plataforma profesional de evaluaciones por challenges*
