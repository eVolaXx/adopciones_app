# 🐾 Portal de Adopciones

Portal web en tiempo real para que protectoras de animales y clínicas veterinarias gestionen adopciones de perros. Permite publicar animales disponibles, recibir solicitudes de adopción y comunicar cambios de estado instantáneamente a través de WebSockets.

---

## ✨ Características principales

- **Catálogo público** de animales con filtros por raza, tamaño, sexo y búsqueda por texto
- **Flujo completo de adopción** con máquina de estados auditada (pendiente → revisión → entrevista → aprobada → completada)
- **Tiempo real** — los cambios de estado se propagan instantáneamente a todos los usuarios conectados vía WebSockets
- **Multi-protectora** — cada organización gestiona sus propios animales y solicitudes de forma aislada
- **Subida de fotos** con redimensionado automático y CDN global (Cloudinary)
- **Notificaciones** persistentes con badge en tiempo real
- **Roles diferenciados**: `super_admin` · `shelter_admin` · `applicant`
- **API documentada** automáticamente en `/docs` (Swagger UI)

---

## 🛠 Stack tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Backend | Python 3.11 + FastAPI | Async nativo, WebSockets built-in, OpenAPI automático |
| Base de datos | PostgreSQL 15 | JSONB para datos flexibles, transacciones ACID |
| Cache / Pub-Sub | Redis 7 | Bus de eventos WebSocket entre workers |
| Almacén de fotos | Cloudinary | 25 GB gratis, CDN incluido, transformaciones automáticas |
| Frontend | React 18 + Vite + TailwindCSS | Hooks para WS, Zustand para estado global |
| Auth | JWT + bcrypt | Stateless, access token (30 min) + refresh token (7 días) |
| Email | SendGrid | 100 emails/día gratis en tier gratuito |
| Despliegue | Docker + Railway | Un comando para levantar todo, SSL automático |

---

## 📁 Estructura del proyecto

```
portal-adopciones/
├── backend/
│   ├── app/
│   │   ├── main.py                     # Entrada principal FastAPI
│   │   ├── api/v1/endpoints/           # auth · animals · adoptions · websocket
│   │   ├── core/                       # config · security · dependencies
│   │   ├── db/
│   │   │   ├── models/                 # SQLAlchemy: Shelter · User · Animal · Adoption
│   │   │   ├── schemas/                # Pydantic: validación de entrada/salida
│   │   │   └── crud/                   # Operaciones de base de datos
│   │   ├── services/                   # email · storage (Cloudinary) · match
│   │   └── websocket/                  # manager · events (Redis pub/sub)
│   ├── tests/                          # pytest + httpx async
│   ├── alembic/                        # Migraciones de base de datos
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                 # AnimalCard · AdoptionForm · StatusBadge
│   │   ├── pages/                      # Home · AnimalDetail · Dashboard · Admin
│   │   ├── hooks/                      # useWebSocket · useAnimals · useAuth
│   │   ├── services/                   # api.js · websocket.js
│   │   └── store/                      # Zustand: estado global
│   └── package.json
├── nginx/default.conf
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Inicio rápido

### Requisitos previos

- Docker y Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Clonar y configurar variables de entorno

```bash
git clone https://github.com/tu-usuario/portal-adopciones.git
cd portal-adopciones
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
DATABASE_URL=postgresql+asyncpg://admin:secretpass@localhost:5432/adopciones_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=genera-uno-con-python-secrets-token-hex-32
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
SENDGRID_API_KEY=tu_sendgrid_key
```

### 2. Levantar servicios con Docker

```bash
docker-compose up -d
```

Esto levanta PostgreSQL 15 en el puerto 5432 y Redis 7 en el puerto 6379.

### 3. Instalar dependencias del backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Crear las tablas en la base de datos

```bash
alembic upgrade head
```

### 5. Arrancar el servidor de desarrollo

```bash
uvicorn app.main:app --reload --port 8000
```

API disponible en `http://localhost:8000`
Documentación Swagger en `http://localhost:8000/docs`

### 6. Arrancar el frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en `http://localhost:5173`

---

## 🗄 Esquema de base de datos

El sistema tiene 6 tablas principales:

```
SHELTERS ──── USERS ──────────── ADOPTIONS ──── ADOPTION_STATUS_LOG
    │                                │
    └──── ANIMALS ──────────────────┘
                                     │
                              NOTIFICATIONS
```

- `SHELTERS` — protectoras y veterinarias
- `USERS` — admins de shelter y familias adoptantes
- `ANIMALS` — perros disponibles con fotos (JSONB) e info de salud (JSONB)
- `ADOPTIONS` — solicitudes con máquina de estados auditada
- `ADOPTION_STATUS_LOG` — historial completo de cada cambio de estado
- `NOTIFICATIONS` — notificaciones persistentes con índice de no leídas

---

## ⚡ WebSockets en tiempo real

El sistema usa el patrón **Room-based WebSocket con Redis Pub/Sub**:

```
Cliente React  ←──WebSocket──→  FastAPI WS Manager
                                       ↕  pub/sub
                               Redis (canal por shelter)
                                       ↕
                               API REST → PostgreSQL
```

Cada protectora tiene su propio canal `ws:shelter:{id}`. Cuando un admin cambia el estado de una solicitud, el evento se publica en Redis y llega instantáneamente a todos los navegadores conectados a ese canal sin polling.

---

## 🧪 Tests

```bash
# Crear la base de datos de test (solo una vez)
docker exec -it adopciones_app-db-1 psql -U admin -d postgres -c "CREATE DATABASE adopciones_test;"

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest tests/ -v

# Solo tests de modelos
pytest tests/test_models.py -v

# Solo tests de autenticación
pytest tests/test_auth.py -v

# Con cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

La suite usa rollback automático por test — cada test trabaja en una transacción que se deshace al finalizar, dejando la base de datos limpia sin truncar tablas manualmente.

---

## 📋 Fases de desarrollo

- [ ] **Fase 1** — Modelos de BD, autenticación JWT, roles
- [ ] **Fase 2** — API REST completa (animales, adopciones, fotos)
- [ ] **Fase 3** — WebSockets y notificaciones en tiempo real
- [ ] **Fase 4** — Frontend React
- [ ] **Fase 5** — Despliegue, CI/CD, monitorización

---

## 🌍 Despliegue en producción

El proyecto está preparado para desplegarse en **Railway** con un coste mensual de ~20-30€:

```bash
# Variables de entorno en Railway (panel web)
DATABASE_URL=postgresql+asyncpg://...   # Railway PostgreSQL
REDIS_URL=redis://...                   # Railway Redis
SECRET_KEY=...
# resto de variables del .env
```

El frontend se despliega en **Vercel** (gratuito) conectado al repositorio GitHub.

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE) para más detalles.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor abre un issue antes de enviar un pull request para discutir el cambio propuesto.
