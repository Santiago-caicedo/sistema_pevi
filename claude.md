# Sistema PEVI - Plataforma de Auditorías Energéticas

## Descripción General

Sistema web de gestión de auditorías energéticas para el programa PEVI (Programa de Eficiencia Energética) coordinado por UPME Colombia. Permite a centros universitarios registrar, analizar y reportar consumos energéticos de empresas auditadas.

**Stack tecnológico:** Django 5.2.8 + PostgreSQL + Bootstrap 5 + Chart.js + WeasyPrint + Anime.js + Leaflet

**Producción:** https://pevicolombia.com (AWS EC2 + S3)

**Centros PEVI:** Universidad del Atlántico, UAO, U. de Vigo, UTP, UFPS

---

## Quick Start

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o en Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env (ya existe con valores por defecto)
# DB: pevi_db, Usuario: postgres, Password: Naranja123

# Ejecutar migraciones
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

---

## Arquitectura del Proyecto

```
sistema_pevi/
├── config/                    # Configuración Django
│   ├── settings.py           # Config global (BD, apps, middleware, S3)
│   ├── middleware.py         # CSP Headers y seguridad HTTP
│   ├── urls.py               # Enrutamiento principal
│   └── wsgi.py               # Punto de entrada WSGI
│
├── gestion/                   # APP CORE: Usuarios, Proyectos, Dashboard
│   ├── models.py             # Usuario, CentroPevi, RegistroActividad
│   ├── views.py              # ~45 vistas principales (~1630 líneas)
│   ├── forms.py              # Formularios con validación de seguridad
│   ├── decorators.py         # Control de acceso RBAC
│   ├── backends.py           # Auth por email O username
│   ├── logger.py             # Funciones de logging reutilizables
│   └── signals.py            # Signals para login/logout automático
│
├── auditorias/                # APP: Datos de Auditorías Energéticas
│   ├── models.py             # Empresa, ProyectoAuditoria, 6 fuentes energéticas, OportunidadMejora
│   ├── forms.py              # Formularios de registro energético + OportunidadMejoraForm
│   └── management/commands/  # Comandos personalizados
│       └── recalcular_kwh.py # Recalcula kWh de registros existentes
│
├── metricas/                  # APP: Dashboards de BI
│   └── views.py              # dashboard_estrategico, dashboard_nacional
│
├── web/                       # APP: Sitio Público
│   ├── models.py             # Noticia
│   └── views.py              # home, nosotros, centros, biblioteca, resultados
│
├── templates/                 # Templates Django (35 archivos)
│   ├── layouts/              # base.html (app), base_public.html (web)
│   ├── gestion/              # Dashboard, CRUD, listados, informes PDF (11 templates)
│   ├── metricas/             # Dashboards BI (2 templates)
│   ├── control/              # Panel superadmin CRUD (7 templates)
│   ├── registration/         # Login + password reset flow (6 templates)
│   ├── web/                  # Landing page, centros con modals (5 templates)
│   └── components/           # Componentes reutilizables (breadcrumbs)
│
├── static/                    # Archivos estáticos (CSS, JS, imágenes)
├── media/                     # Archivos subidos (documentos de proyectos)
├── logs/                      # Logs del sistema (acceso, actividad, seguridad, errores)
└── requirements.txt           # Dependencias Python
```

---

## Modelo de Datos Principal

### Entidades Core

```
CentroPevi (1) ─────┬────> (N) Usuario
                    ├────> (N) Empresa (aislamiento por centro)
                    └────> (N) ProyectoAuditoria

Usuario (1) ────────┬────> (N) ProyectoAuditoria [lider_proyecto]
                    └────> (M:N) ProyectoAuditoria.equipo

Empresa (1) ────────────> (N) ProyectoAuditoria

ProyectoAuditoria (1) ──┬─> (1) Electricidad
                        ├─> (1) GasNatural
                        ├─> (1) CarbonMineral
                        ├─> (1) FuelOil
                        ├─> (1) Biomasa
                        ├─> (1) GasPropano
                        ├─> (N) DocumentoProyecto
                        └─> (N) OportunidadMejora

Noticia ────────────────────> (1) Usuario [autor]
```

> **Nota:** La relación 1:1 entre ProyectoAuditoria y fuentes energéticas NO está enforceada por constraint de unicidad en BD. Se asume vía `.first()` en queries.

### Sistema de Roles (Jerárquico)

| Rol | Código | Permisos |
|-----|--------|----------|
| Director Nacional | `DIRECTOR_NACIONAL` | Acceso total, visión país, tablero nacional |
| Director Centro | `DIRECTOR_CENTRO` | Gestión de su centro, métricas BI |
| Profesor | `PROFESOR` | Lidera proyectos, gestiona empresas |
| Estudiante | `ESTUDIANTE` | Participa en equipos asignados |

**Patrón de Rol Híbrido:** Un `DIRECTOR_NACIONAL` con `centro_pevi` asignado actúa también como director de ese centro (ve vista de centro en dashboard, property `es_director_centro` retorna True). Esto permite que un Nacional gestione un centro específico sin perder acceso global.

### Estados y Fases de Proyecto

```
Estados: BORRADOR → EJECUCION → REVISION → FINALIZADO

Fases (opcional): FASE_1, FASE_2, FASE_3, FASE_4
```

---

## Conversión de Energía (Crítico)

El sistema convierte combustibles a kWh equivalente en `CombustibleBase.save()`:

### Fórmula General
```python
Energía (kJ) = consumo_orig × factor_unidad × poder_calorífico × factor_energia
Energía (kWh) = Energía (kJ) / 3600
```

### Unidades por Tipo de Energético

| Energético | Consumo | Poder Calorífico | Factor Emisión | factor_unidad | factor_energia |
|------------|---------|------------------|----------------|---------------|----------------|
| **Electricidad** | kWh | N/A | kgCO2/kWh | - | - |
| **Gas Natural** | m³ | kJ/m³ | kgCO2/m³ | 1.0 | 1.0 |
| **Carbón Mineral** | Ton | MJ/kg | kgCO2/Ton | 1000 (→kg) | 1000 (MJ→kJ) |
| **Fuel Oil** | Gal | MJ/usgal | kgCO2/Gal | 1.0 | 1000 (MJ→kJ) |
| **Biomasa** | Ton | kJ/kg | kgCO2/Ton | 1000 (→kg) | 1.0 |
| **Gas Propano (GLP)** | kg | MJ/kg | kgCO2/kg | 1.0 | 1000 (MJ→kJ) |

### Cálculo de Emisiones
```python
# IMPORTANTE: Las emisiones NO se auto-calculan en save().
# El campo emisiones_totales es ENTRADA MANUAL del usuario.
# La fórmula teórica es: (consumo_anual_orig × factor_emision) / 1000
# El JavaScript en registro_energia_form.html calcula esto en tiempo real
# como SUGERENCIA visual, pero el usuario puede editar el valor final.
# No hay validación server-side de la fórmula de emisiones.
```

### Comando para Recalcular Datos Existentes
```bash
# Ver cambios sin aplicar
python manage.py recalcular_kwh --dry-run

# Aplicar corrección a todos los registros
python manage.py recalcular_kwh
```

---

## Archivos Clave por Funcionalidad

### Autenticación y Seguridad
- `gestion/backends.py` - Login por email O username
- `gestion/decorators.py` - `@solo_directivos`, `@solo_lideres`, `@acceso_staff`
- `gestion/forms.py` - Validación anti-escalada de privilegios en `UsuarioForm.clean_rol()`

### Lógica de Negocio Principal
- `gestion/views.py` - `verificar_acceso_proyecto()` - Control de acceso por proyecto
- `gestion/views.py` - `FORM_MAPPING` - Configuración de formularios energéticos
- `auditorias/models.py` - `CombustibleBase.save()` - Conversión automática a kWh

### Registro de Energía
- `auditorias/forms.py` - `RegistroEnergiaForm` - Intercepta comas en números (1,200 → 1200)
- `templates/gestion/registro_energia_form.html` - Formulario con cálculo JS en tiempo real

### Expediente de Proyecto (Detalle)
- `gestion/views.py` - `detalle_proyecto()` - KPIs y datos para 4 gráficos + oportunidades de mejora
- `templates/gestion/proyecto_detalle.html` - 4 gráficos Chart.js:
  1. Matriz de Consumo (kWh) - doughnut
  2. Huella de Carbono (TonCO2) - doughnut
  3. Balance Térmico (MBTU) - barras
  4. Distribución de Costos - barras

### Oportunidades de Mejora (Reducción Energética)

**Sistema 1: Reducción por Fuente Energética (% global)**
- `auditorias/models.py` - `FuenteEnergiaBase`:
  - `porcentaje_reduccion` - Meta de reducción (%) por energético
  - `get_ahorro_energia_potencial()` - Calcula kWh ahorrables
  - `get_ahorro_costo_potencial()` - Calcula COP ahorrables
  - `get_ahorro_emisiones_potencial()` - Calcula TonCO2 evitables
- `gestion/views.py` - `guardar_reduccion()` - Guarda % de reducción via AJAX

**Sistema 2: OPM - Oportunidades de Mejora Individuales**
- `auditorias/models.py` - `OportunidadMejora`:
  - Campos: `codigo`, `descripcion`, `energetico` (choices), `ahorro_energia` (kWh/año), `costos_evitados` (MCOP/año), `emisiones_evitadas` (TonCO2/año)
  - Financieros: `inversion` (COP), `vpn` (COP), `tir` (%), `payback` (meses)
  - `observaciones` (TextField)
- `gestion/views.py` - CRUD: `crear_oportunidad()`, `editar_oportunidad()`, `eliminar_oportunidad()`
- `auditorias/forms.py` - `OportunidadMejoraForm` (excluye proyecto, created_at)

**UI en proyecto_detalle.html:**
- Panel de comparación visual (Consumo Actual → Consumo Proyectado)
- 3 KPI boxes (ahorro kWh, COP, TonCO2)
- Gráfico de barras horizontales por fuente energética
- Tabla con % reducción y ahorros calculados
- Modal para editar % de reducción
- Tabla OPM con CRUD inline

### Dashboards y BI
- `metricas/views.py` - `dashboard_estrategico()` - BI con filtros por estado/fecha
- `metricas/views.py` - `dashboard_nacional()` - Visión consolidada país

### Generación de PDF
- `gestion/views.py` - `generar_informe_pdf()` - Reportes con WeasyPrint
- `templates/gestion/informe_pdf.html` - Template del informe

### Sitio Público
- `web/models.py` - `Noticia`: titulo, slug (unique), imagen_portada, resumen, contenido, autor (FK→Usuario), fecha_publicacion, publicada
- `web/views.py` - Vistas públicas (home, nosotros, centros, biblioteca, resultados)
- `templates/web/centros.html` - Modals con gráficos Chart.js por centro (estados, evolución temporal)
- `templates/web/resultados.html` - Hero section con glassmorphism + filtros + exportar CSV/PDF + mapa Leaflet/Carto

### Mapa Interactivo (Resultados Públicos)
- `web/views.py` - `resultados()` genera `centros_mapa_json` con lat/lng/nombre/color por centro
- Tiles: `*.basemaps.cartocdn.com` (CSP configurado en img-src)
- Filtros: año, región, sector productivo

### Auto-asignación de Líder de Proyecto
- `gestion/views.py` - `crear_proyecto()`:
  - Profesores se auto-asignan como líderes al crear proyectos
  - Campo preseleccionado en GET, validado en POST

---

## Rutas Principales

```python
# ==================== APP INTERNA ====================

# Dashboard y listados
/app/                                → dashboard
/app/proyectos/                      → lista_proyectos (filtros: estado, fase, centro, líder)
/app/proyectos/<id>/                 → detalle_proyecto (4 gráficos + bitácora)

# CRUD Proyectos
/app/proyectos/nuevo/                → crear_proyecto
/app/proyectos/<id>/editar/          → editar_proyecto
/app/proyectos/<id>/estado/<estado>/ → cambiar_estado_proyecto

# Registro de energía (bitácora)
/app/proyectos/<id>/registro/produccion/         → registrar_produccion
/app/proyectos/<id>/registro/<tipo_energia>/     → registrar_consumo
# tipo_energia: electricidad, gas_natural, carbon, fuel_oil, biomasa, gas_propano

# Documentos e Informes
/app/proyectos/<id>/documentos/subir/  → subir_documento
/app/proyectos/<id>/informe/pdf/       → generar_informe_pdf

# Oportunidades de Mejora
/app/proyectos/<id>/reduccion/                       → guardar_reduccion (AJAX)
/app/proyectos/<id>/oportunidades/nueva/             → crear_oportunidad
/app/proyectos/<id>/oportunidades/<opm_id>/editar/   → editar_oportunidad
/app/proyectos/<id>/oportunidades/<opm_id>/eliminar/ → eliminar_oportunidad

# Gestión administrativa
/app/empresas/                       → lista_empresas
/app/empresas/nueva/                 → crear_empresa
/app/empresas/<id>/editar/           → editar_empresa
/app/equipo/                         → lista_usuarios
/app/equipo/nuevo/                   → crear_usuario
/app/equipo/<id>/editar/             → editar_usuario
/app/equipo/<id>/eliminar/           → eliminar_usuario

# Métricas BI (solo directivos)
/app/metricas/estrategico/           → dashboard_estrategico
/app/metricas/nacional/              → dashboard_nacional

# Super Admin - Control Panel
/app/control/                              → control_panel
/app/control/centros/                      → control_centros_lista
/app/control/centros/nuevo/                → control_centro_crear
/app/control/centros/<id>/editar/          → control_centro_editar
/app/control/centros/<id>/eliminar/        → control_centro_eliminar
/app/control/usuarios/                     → control_usuarios_lista
/app/control/usuarios/nuevo/               → control_usuario_crear
/app/control/usuarios/<id>/editar/         → control_usuario_editar
/app/control/usuarios/<id>/eliminar/       → control_usuario_eliminar
/app/control/noticias/                     → control_noticias_lista
/app/control/noticias/nueva/               → control_noticia_crear
/app/control/noticias/<id>/editar/         → control_noticia_editar
/app/control/noticias/<id>/eliminar/       → control_noticia_eliminar
/admin/                                    → Django Admin

# ==================== AUTENTICACIÓN ====================

/accounts/password_reset/                  → password_reset_form
/accounts/password_reset/done/             → password_reset_done
/accounts/reset/<uidb64>/<token>/          → password_reset_confirm
/accounts/reset/done/                      → password_reset_complete

# ==================== SITIO PÚBLICO ====================

/                                    → home_public (landing)
/nosotros/                           → nosotros
/centros/                            → centros_public (con modals)
/biblioteca/                         → biblioteca
/resultados/                         → resultados_public (filtros + exportar)
```

---

## Patrones de Seguridad

### Capas de Protección (en orden)
1. `@login_required` - Requiere sesión activa
2. `@acceso_staff` / `@solo_directivos` / `@solo_lideres` - Valida rol
3. `verificar_acceso_proyecto()` - Valida ownership del proyecto
4. `PermissionDenied` - Error 403 si no cumple

### Validación Anti-Escalada
```python
# En UsuarioForm (gestion/forms.py)
# Director Centro solo puede crear PROFESOR y ESTUDIANTE
# Validación en clean_rol() bloquea intentos de crear Directores
```

### Aislamiento de Datos por Centro
- Empresas filtradas por `centro` del usuario
- Proyectos filtrados por `centro` del usuario
- Usuarios filtrados por `centro_pevi` del usuario
- Director Nacional y Superuser ven todo

### Máquina de Estados de Proyectos
```python
# Transiciones válidas (gestion/views.py - cambiar_estado_proyecto)
TRANSICIONES_VALIDAS = {
    'BORRADOR': ['EJECUCION'],
    'EJECUCION': ['REVISION', 'BORRADOR'],
    'REVISION': ['FINALIZADO', 'EJECUCION'],
    'FINALIZADO': [],  # Estado terminal
}
```

### Validaciones de Seguridad Implementadas
- Director Centro NO puede editar a otro Director o superior
- Empresas siempre requieren centro asignado
- Director Nacional NO puede mezclar centros (empresa de un centro + equipo de otro)
- Usuarios (excepto Nacional) siempre requieren centro asignado
- Advertencia al transferir liderazgo de proyecto (doble confirmación)
- Transacciones atómicas en crear/editar proyecto

### Content Security Policy (CSP Headers)

El sistema implementa CSP para prevenir ataques XSS. Configurado en `config/middleware.py`.

**Directivas CSP completas:**

| Directiva | Fuentes |
|-----------|---------|
| `script-src` | `'self'`, `'unsafe-inline'`, `cdn.jsdelivr.net`, `cdnjs.cloudflare.com` |
| `style-src` | `'self'`, `'unsafe-inline'`, `cdn.jsdelivr.net`, `cdnjs.cloudflare.com`, `fonts.googleapis.com` |
| `font-src` | `'self'`, `fonts.gstatic.com`, `cdn.jsdelivr.net` |
| `img-src` | `'self'`, `data:`, `vadomdata.s3.amazonaws.com`, `p4.wallpaperbetter.com`, `wallpapers.com`, `img.freepik.com`, `lirp.cdn-website.com`, `*.basemaps.cartocdn.com` |
| `connect-src` | `'self'`, `cdn.jsdelivr.net` |
| `frame-ancestors` | `'none'` |
| `form-action` | `'self'` |
| `base-uri` | `'self'` |
| `object-src` | `'none'` |

**Fuentes externas por uso:**
| Dominio | Uso |
|---------|-----|
| `cdn.jsdelivr.net` | Bootstrap CSS/JS, Icons, Chart.js |
| `cdnjs.cloudflare.com` | Anime.js (animaciones sitio público) |
| `fonts.googleapis.com` / `fonts.gstatic.com` | Google Fonts (Inter) |
| `vadomdata.s3.amazonaws.com` | S3 producción (estáticos/media) |
| `p4.wallpaperbetter.com`, `wallpapers.com`, `img.freepik.com` | Imágenes hero landing |
| `lirp.cdn-website.com` | Imágenes sección landing |
| `*.basemaps.cartocdn.com` | Tiles del mapa (resultados públicos) |

**Headers de seguridad adicionales:**
- `X-Content-Type-Options: nosniff` - Previene MIME sniffing
- `X-Frame-Options: DENY` - Previene clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin` - Control de referrer

**Si agregas una nueva librería externa o imagen externa:**
1. Editar `config/middleware.py`
2. Agregar el dominio a la directiva correspondiente (script-src, style-src, img-src, etc.)
3. Actualizar esta documentación

---

## Sistema de Logs

### Archivos de Log
| Archivo | Contenido | Ubicación |
|---------|-----------|-----------|
| `acceso.log` | Login, logout, intentos fallidos | `logs/` |
| `actividad.log` | Crear, editar, eliminar (CRUD) | `logs/` |
| `seguridad.log` | Accesos denegados, escaladas bloqueadas | `logs/` |
| `errores.log` | Excepciones del sistema | `logs/` |

### Modelo RegistroActividad
```python
# gestion/models.py - Logs en base de datos
RegistroActividad:
    - tipo: ACCESO | ACTIVIDAD | SEGURIDAD | ERROR
    - accion: LOGIN | LOGOUT | CREAR | EDITAR | ELIMINAR | ACCESO_DENEGADO
    - usuario, timestamp, ip_address, user_agent
    - modelo_afectado, objeto_id, objeto_repr
    - descripcion, centro
```

### Módulo de Logging
```python
# gestion/logger.py - Funciones disponibles
from gestion.logger import (
    log_login, log_logout, log_login_fallido,  # Acceso
    log_crear, log_editar, log_eliminar,        # Actividad
    log_acceso_denegado, log_escalada_bloqueada, # Seguridad
    log_cambio_estado, log_error                 # Otros
)
```

### Signals Automáticos
- `gestion/signals.py` - Captura login/logout automáticamente via Django signals
- Se registran en `gestion/apps.py` al iniciar la app

### Configuración (settings.py)
- `LOGGING` configurado con `RotatingFileHandler` (5-10 MB por archivo)
- Hasta 10 backups por archivo
- Logs visibles en Django Admin (solo lectura)

### Mantenimiento de Logs
```bash
# Limpiar logs de BD mayores a 90 días
python manage.py shell -c "
from gestion.models import RegistroActividad
from django.utils import timezone
from datetime import timedelta
fecha_limite = timezone.now() - timedelta(days=90)
RegistroActividad.objects.filter(timestamp__lt=fecha_limite).delete()
"
```

### Producción - Permisos
```bash
# La carpeta logs/ debe existir con permisos para www-data
sudo mkdir -p /opt/sistema_pevi/logs
sudo chown www-data:www-data /opt/sistema_pevi/logs
sudo chmod 775 /opt/sistema_pevi/logs

# Crear archivos iniciales
sudo touch /opt/sistema_pevi/logs/{acceso,actividad,errores,seguridad}.log
sudo chown www-data:www-data /opt/sistema_pevi/logs/*.log
```

---

## Indicadores Clave (KPIs)

| KPI | Fórmula | Uso |
|-----|---------|-----|
| Energía Total | Σ(kWh eléctricos + kWh térmicos) | Dashboard, matriz |
| IDES | Energía_Total / Producción_Total | Desempeño energético |
| Emisiones | Σ(emisiones_totales) por fuente (entrada manual) | Huella de carbono (TonCO2) |
| Costo Normalizado | Costo_Total / Energía_kWh | Comparativas ($/kWh) |
| Ahorro Potencial kWh | Σ(kWh × %reducción) / 100 | Oportunidades de mejora |
| Ahorro Potencial COP | Σ(costo_anual × %reducción) / 100 | Impacto económico |
| CO2 Evitado | Σ(emisiones × %reducción) / 100 | Impacto ambiental |

---

## Tecnologías Frontend

- **Framework CSS:** Bootstrap 5.3.0 (CDN)
- **Iconos:** Bootstrap Icons 1.11.0
- **Gráficas:** Chart.js 4.4.1 (dona con porcentajes, barras, barras horizontales)
- **Animaciones:** Anime.js (scroll animations, counters, stagger en sitio público)
- **Mapas:** Leaflet + Carto tiles (página de resultados públicos)
- **Fuente:** Inter (Google Fonts)
- **Templates:** Django Template Language (Jinja2-like)

### Paleta de Colores
```css
--sidebar-bg: #0f172a;        /* Azul oscuro (slate-900) */
--sidebar-active: #38bdf8;    /* Cyan (sky-400) */
--primary-brand: #0284c7;     /* Azul (sky-600) */
--body-bg: #f1f5f9;           /* Gris claro (slate-100) */
```

### Clases CSS Personalizadas
- `.card-modern` - Tarjetas con sombra suave
- `.table-modern` - Tablas estilizadas
- `.badge-soft` / `.bg-soft-*` - Badges con colores suaves
- `.hover-lift` - Efecto elevación al hover

---

## Almacenamiento de Archivos (Híbrido Local/S3)

| Entorno | DEBUG | Almacenamiento | Rutas |
|---------|-------|----------------|-------|
| **Desarrollo** | `True` | Sistema local | `/static/`, `/media/` |
| **Producción** | `False` | AWS S3 | `vadomdata/pevi/static/`, `vadomdata/pevi/media/` |

### Variables de Entorno (.env)
```bash
# Desarrollo
DEBUG=True
DB_NAME=pevi_db
DB_USER=postgres
DB_PASSWORD=Naranja123
DB_HOST=localhost
DB_PORT=5432

# Producción
DEBUG=False
S3_CLIENT_PREFIX=pevi
# Credenciales AWS via IAM Role del EC2
```

### Email SMTP
```python
EMAIL_HOST = 'mail.vadomdata.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'info@vadomdata.com'  # Configurable via .env
DEFAULT_FROM_EMAIL = 'PEVI Colombia <info@vadomdata.com>'
```

---

## Comandos Útiles

```bash
# === DESARROLLO ===
python manage.py runserver
python manage.py shell
python manage.py createsuperuser

# === MIGRACIONES ===
python manage.py makemigrations
python manage.py migrate

# === ESTÁTICOS ===
python manage.py collectstatic          # Desarrollo (./staticfiles/)
python manage.py collectstatic --noinput # Producción (S3)

# === MANTENIMIENTO ===
python manage.py recalcular_kwh --dry-run  # Ver cambios en kWh
python manage.py recalcular_kwh            # Aplicar corrección

# === ADMIN ===
# http://localhost:8000/admin/
```

---

## Notas de Desarrollo

### Al modificar modelos
1. `python manage.py makemigrations <app>`
2. Revisar la migración generada
3. `python manage.py migrate`
4. Si solo cambias lógica en `save()`, no necesitas migración

### Al agregar vistas
1. Aplicar decorador de seguridad (`@login_required`, `@acceso_staff`, etc.)
2. Usar `verificar_acceso_proyecto()` para operaciones sobre proyectos
3. Pasar `user=request.user` a formularios que validen jerarquía

### Al agregar fuentes energéticas
1. Crear modelo heredando de `CombustibleBase` o `FuenteEnergiaBase`
2. Definir `factor_unidad` y `factor_energia` en `save()` del modelo padre
3. Crear formulario heredando de `RegistroEnergiaForm`
4. Agregar entrada en `FORM_MAPPING` (gestion/views.py)
5. Actualizar JavaScript en `registro_energia_form.html` (factores por tipo)
6. Agregar lógica de agregación en dashboards y gráficos

### Formularios con números
- Heredar de `RegistroEnergiaForm` (intercepta comas automáticamente)
- Campos numéricos usan `TextInput` para permitir formato visual
- JavaScript calcula en tiempo real los campos derivados
- Variable `tipo_energia` (no `titulo_energia`) para detectar factores

### Chart.js en Modals
- Inicializar gráficos en evento `shown.bs.modal`, no en `DOMContentLoaded`
- Destruir instancia anterior antes de crear nueva (`chart.destroy()`)

### Glassmorphism en Hero Sections
- Usar `backdrop-filter: blur()` con `background: rgba(255,255,255,0.1)`
- Agregar shapes animados con `@keyframes float`
- Overlay grid pattern: `background-image: linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px)`

### Notificaciones (Messages)
- Configurado `MESSAGE_TAGS` en settings.py para Bootstrap
- Block de mensajes en `templates/layouts/base.html`
- Usar `messages.success()`, `messages.error()`, etc. en vistas

### Transferencia de Liderazgo de Proyecto
- `editar_proyecto()` implementa patrón de doble-POST para profesores
- Primer POST: detecta cambio de líder → muestra advertencia + `confirmar_cambio_lider=True`
- Segundo POST: requiere `confirmar_cambio_lider` en POST data para aplicar
- No usa token/timestamp, si el usuario navega entre POSTs se pierde la confirmación

### Control Panel (Superadmin)
- Protegido por `@solo_superadmin` (verifica `is_superuser`, no rol)
- CRUD completo para: CentroPevi, Usuario (con password + is_superuser), Noticia
- Forms especializados: `CentroPeviForm` (23 campos), `UsuarioAdminForm`, `NoticiaAdminForm`
- Templates en `templates/control/` (7 archivos)

### Herencia de Modelos Energéticos
```
FuenteEnergiaBase (abstract)
├── Electricidad (concreto) - consumo directo en kWh
└── CombustibleBase (abstract) - conversión automática en save()
    ├── GasNatural
    ├── CarbonMineral
    ├── FuelOil
    ├── Biomasa (campo extra: tipo)
    └── GasPropano
```
- `related_name="%(class)s_related"` genera: electricidad_related, gasnatural_related, etc.
- Acceso polimórfico: `hasattr(fuente, 'consumo_anual_kwh')` vs `consumo_anual` (Electricidad)

### CentroPevi - Campos Detallados
Modelo con 23+ campos organizados en secciones:
- **Identificación:** nombre, nombre_corto (siglas), codigo_interno, activo
- **Branding:** logo, imagen_portada, color_primario (hex)
- **Ubicación:** region, ciudad, direccion, latitud, longitud (para mapa)
- **Contacto:** email_contacto, telefono, sitio_web
- **Redes:** linkedin, twitter, instagram
- **Director:** director_nombre, director_cargo, director_foto, director_email
- **Métricas:** estudiantes_formados, año_vinculacion
- **Properties:** proyectos_count, proyectos_finalizados_count, empresas_atendidas_count

### Decoradores de Acceso
| Decorador | Roles Permitidos | Uso |
|-----------|-----------------|-----|
| `@acceso_staff` | Todos (EST, PROF, DIR_C, DIR_N) | Acceso general app |
| `@solo_lideres` | PROF, DIR_C, DIR_N | Crear proyectos/empresas |
| `@solo_directivos` | DIR_C, DIR_N | Gestionar usuarios |
| `@solo_superadmin` | is_superuser=True | Control panel |

> Todos permiten superuser automáticamente (God Mode)

---

## Despliegue en Producción

```bash
# En el servidor EC2
cd /opt/sistema_pevi
source venv/bin/activate
git pull origin main

# Si hay cambios en modelos:
python manage.py migrate

# Si hay cambios en estáticos:
python manage.py collectstatic --noinput

# Si hay cambios en conversión de energía:
python manage.py recalcular_kwh

# Reiniciar servicio (Apache en este servidor)
sudo systemctl restart apache2
```

### Primera vez - Configurar Logs
```bash
# Crear carpeta y archivos de log con permisos correctos
sudo mkdir -p /opt/sistema_pevi/logs
sudo touch /opt/sistema_pevi/logs/{acceso,actividad,errores,seguridad}.log
sudo chown -R www-data:www-data /opt/sistema_pevi/logs
sudo chmod 775 /opt/sistema_pevi/logs
sudo chmod 644 /opt/sistema_pevi/logs/*.log
```

### Logs del Servidor
| Log | Ubicación | Uso |
|-----|-----------|-----|
| Apache errors | `/var/log/apache2/pevicolombia_error.log` | Errores de infraestructura |
| App acceso | `/opt/sistema_pevi/logs/acceso.log` | Login/logout usuarios |
| App actividad | `/opt/sistema_pevi/logs/actividad.log` | CRUD de datos |
| App seguridad | `/opt/sistema_pevi/logs/seguridad.log` | Accesos denegados |
