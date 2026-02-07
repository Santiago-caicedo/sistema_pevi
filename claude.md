# Sistema PEVI - Plataforma de Auditorías Energéticas

## Descripción General

Sistema web de gestión de auditorías energéticas para el programa PEVI (Programa de Eficiencia Energética) coordinado por UPME Colombia. Permite a centros universitarios registrar, analizar y reportar consumos energéticos de empresas auditadas.

**Stack tecnológico:** Django 5.2.8 + PostgreSQL + Bootstrap 5 + Chart.js + WeasyPrint

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
│   ├── urls.py               # Enrutamiento principal
│   └── wsgi.py               # Punto de entrada WSGI
│
├── gestion/                   # APP CORE: Usuarios, Proyectos, Dashboard
│   ├── models.py             # Usuario (AbstractUser), CentroPevi
│   ├── views.py              # 36 vistas principales (~1100 líneas)
│   ├── forms.py              # Formularios con validación de seguridad
│   ├── decorators.py         # Control de acceso RBAC
│   └── backends.py           # Auth por email O username
│
├── auditorias/                # APP: Datos de Auditorías Energéticas
│   ├── models.py             # Empresa, ProyectoAuditoria, 6 fuentes energéticas
│   ├── forms.py              # Formularios de registro energético
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
├── templates/                 # Templates Django (~25 archivos)
│   ├── layouts/              # base.html (app), base_public.html (web)
│   ├── gestion/              # Dashboard, CRUD, listados, informes PDF
│   ├── metricas/             # Dashboards BI
│   ├── registration/         # Login (5 logos universidades)
│   └── web/                  # Landing page, centros con modals
│
├── static/                    # Archivos estáticos (CSS, JS, imágenes)
├── media/                     # Archivos subidos (documentos de proyectos)
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
                        └─> (N) DocumentoProyecto
```

### Sistema de Roles (Jerárquico)

| Rol | Código | Permisos |
|-----|--------|----------|
| Director Nacional | `DIRECTOR_NACIONAL` | Acceso total, visión país, tablero nacional |
| Director Centro | `DIRECTOR_CENTRO` | Gestión de su centro, métricas BI |
| Profesor | `PROFESOR` | Lidera proyectos, gestiona empresas |
| Estudiante | `ESTUDIANTE` | Participa en equipos asignados |

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
# Las emisiones se calculan sobre el consumo ORIGINAL, NO sobre kWh
Emisiones (TonCO2) = (consumo_anual_orig × factor_emision) / 1000
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
- `gestion/views.py` - `detalle_proyecto()` - KPIs y datos para 4 gráficos
- `templates/gestion/proyecto_detalle.html` - 4 gráficos Chart.js:
  1. Matriz de Consumo (kWh) - doughnut
  2. Huella de Carbono (TonCO2) - doughnut
  3. Balance Térmico (MBTU) - barras
  4. Distribución de Costos - barras

### Dashboards y BI
- `metricas/views.py` - `dashboard_estrategico()` - BI con filtros por estado/fecha
- `metricas/views.py` - `dashboard_nacional()` - Visión consolidada país

### Generación de PDF
- `gestion/views.py` - `generar_informe_pdf()` - Reportes con WeasyPrint
- `templates/gestion/informe_pdf.html` - Template del informe

### Sitio Público
- `web/views.py` - Vistas públicas (home, nosotros, centros, biblioteca, resultados)
- `templates/web/centros.html` - Modals con gráficos Chart.js por centro
- `templates/web/resultados.html` - Filtros (año, región, sector) + exportar CSV/PDF

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

# Gestión administrativa
/app/empresas/                       → lista_empresas
/app/empresas/nueva/                 → crear_empresa
/app/equipo/                         → lista_usuarios
/app/equipo/nuevo/                   → crear_usuario
/app/equipo/<id>/editar/             → editar_usuario

# Métricas BI (solo directivos)
/app/metricas/estrategico/           → dashboard_estrategico
/app/metricas/nacional/              → dashboard_nacional

# Super Admin
/app/control/                        → control_panel
/admin/                              → Django Admin

# ==================== SITIO PÚBLICO ====================

/                                    → home_public (landing)
/nosotros/                           → nosotros
/centros/                            → centros_public (con modals)
/biblioteca/                         → biblioteca
/resultados/                         → resultados (filtros + exportar)
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

---

## Indicadores Clave (KPIs)

| KPI | Fórmula | Uso |
|-----|---------|-----|
| Energía Total | Σ(kWh eléctricos + kWh térmicos) | Dashboard, matriz |
| IDES | Energía_Total / Producción_Total | Desempeño energético |
| Emisiones | Σ(consumo_orig × factor_emisión) / 1000 | Huella de carbono (TonCO2) |
| Costo Normalizado | Costo_Total / Energía_kWh | Comparativas ($/kWh) |

---

## Tecnologías Frontend

- **Framework CSS:** Bootstrap 5.3.0 (CDN)
- **Iconos:** Bootstrap Icons 1.11.0
- **Gráficas:** Chart.js 4.4.1 (dona con porcentajes, barras)
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

# Producción
DEBUG=False
S3_CLIENT_PREFIX=pevi
# Credenciales AWS via IAM Role del EC2
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

### Notificaciones (Messages)
- Configurado `MESSAGE_TAGS` en settings.py para Bootstrap
- Block de mensajes en `templates/layouts/base.html`
- Usar `messages.success()`, `messages.error()`, etc. en vistas

---

## Despliegue en Producción

```bash
# En el servidor EC2
cd /path/to/sistema_pevi
git pull origin main

# Si hay cambios en modelos:
python manage.py migrate

# Si hay cambios en estáticos:
python manage.py collectstatic --noinput

# Si hay cambios en conversión de energía:
python manage.py recalcular_kwh

# Reiniciar servicio
sudo systemctl restart gunicorn
```
