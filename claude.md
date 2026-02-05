# Sistema PEVI - Plataforma de Auditorías Energéticas

## Descripción General

Sistema web de gestión de auditorías energéticas para el programa PEVI (Programa de Eficiencia Energética) coordinado por UPME Colombia. Permite a centros universitarios registrar, analizar y reportar consumos energéticos de empresas auditadas.

**Stack tecnológico:** Django 5.2.8 + PostgreSQL + Bootstrap 5 + Chart.js + WeasyPrint

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
│   ├── settings.py           # Config global (BD, apps, middleware)
│   ├── urls.py               # Enrutamiento principal
│   └── wsgi.py               # Punto de entrada WSGI
│
├── gestion/                   # APP CORE: Usuarios, Proyectos, Dashboard
│   ├── models.py             # Usuario (AbstractUser), CentroPevi
│   ├── views.py              # 16 vistas principales (28KB)
│   ├── forms.py              # Formularios con validación de seguridad
│   ├── decorators.py         # Control de acceso RBAC
│   └── backends.py           # Auth por email O username
│
├── auditorias/                # APP: Datos de Auditorías Energéticas
│   ├── models.py             # Empresa, ProyectoAuditoria, 6 fuentes energéticas
│   └── forms.py              # Formularios de registro energético
│
├── metricas/                  # APP: Dashboards de BI
│   └── views.py              # dashboard_estrategico, dashboard_nacional
│
├── web/                       # APP: Sitio Público
│   ├── models.py             # Noticia
│   └── views.py              # home, nosotros, centros, biblioteca
│
├── templates/                 # Templates Jinja2 (20 archivos)
│   ├── layouts/              # base.html, base_public.html
│   ├── gestion/              # Dashboard, CRUD, listados
│   ├── metricas/             # Dashboards BI
│   ├── registration/         # Login
│   └── web/                  # Landing page
│
├── static/                    # Archivos estáticos
├── media/                     # Archivos subidos
└── requirements.txt           # 19 dependencias Python
```

---

## Modelo de Datos Principal

### Entidades Core

```
CentroPevi (1) ─────┬────> (N) Usuario
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
| Director Nacional | `DIRECTOR_NACIONAL` | Acceso total, visión país |
| Director Centro | `DIRECTOR_CENTRO` | Gestión de su centro |
| Profesor | `PROFESOR` | Lidera proyectos |
| Estudiante | `ESTUDIANTE` | Participa en equipos |

### Estados de Proyecto

```
BORRADOR → EJECUCION → REVISION → FINALIZADO
```

---

## Archivos Clave por Funcionalidad

### Autenticación y Seguridad
- `gestion/backends.py` - Login por email O username
- `gestion/decorators.py` - `@solo_directivos`, `@solo_lideres`, `@acceso_staff`
- `gestion/forms.py` - Validación anti-escalada de privilegios

### Lógica de Negocio Principal
- `gestion/views.py:73-85` - `verificar_acceso_proyecto()` - Control de acceso por proyecto
- `gestion/views.py:34-71` - `FORM_MAPPING` - Configuración de formularios energéticos
- `auditorias/models.py:206-237` - `CombustibleBase.save()` - Conversión automática a kWh

### Dashboards y BI
- `metricas/views.py:14-221` - `dashboard_estrategico()` - BI con filtros
- `metricas/views.py:225-410` - `dashboard_nacional()` - Visión consolidada

### Generación de PDF
- `gestion/views.py:609-694` - `generar_informe_pdf()` - Reportes con WeasyPrint
- `templates/gestion/informe_pdf.html` - Template del informe

---

## Rutas Principales

```python
# Dashboard y listados
/                                    → dashboard
/proyectos/                          → lista_proyectos
/proyectos/<id>/                     → detalle_proyecto

# CRUD Proyectos
/proyectos/nuevo/                    → crear_proyecto
/proyectos/<id>/editar/              → editar_proyecto
/proyectos/<id>/estado/<estado>/     → cambiar_estado_proyecto

# Registro de energía (bitácora)
/proyectos/<id>/registro/produccion/           → registrar_produccion
/proyectos/<id>/registro/<tipo_energia>/       → registrar_consumo
# tipo_energia: electricidad, gas_natural, carbon, fuel_oil, biomasa, gas_propano

# Documentos
/proyectos/<id>/documentos/subir/    → subir_documento

# Informes
/proyectos/<id>/informe/pdf/         → generar_informe_pdf

# Gestión administrativa
/empresas/                           → lista_empresas
/empresas/nueva/                     → crear_empresa
/equipo/                             → lista_usuarios
/equipo/nuevo/                       → crear_usuario
/equipo/<id>/editar/                 → editar_usuario

# Métricas BI
/metricas/estrategico/               → dashboard_estrategico
/metricas/nacional/                  → dashboard_nacional

# Sitio público
/web/                                → home_public
/web/nosotros/                       → nosotros
/web/centros/                        → centros_public
/web/biblioteca/                     → biblioteca
```

---

## Conversión de Energía

El sistema convierte automáticamente combustibles a kWh equivalente:

```python
# Fórmula en CombustibleBase.save()
Energía (kJ) = consumo_orig × factor_conversión × poder_calorífico
Energía (kWh) = Energía (kJ) / 3600

# Factores de conversión por tipo:
- Gas Natural: 1.0 (m³ directo)
- Carbón/Biomasa: 1000 (Ton → kg)
- Fuel Oil: 0.00378541 (Gal → m³)
- GLP: 1.0 (kg directo)
- Electricidad: Sin conversión (ya en kWh)
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

---

## Indicadores Clave (KPIs)

| KPI | Fórmula | Uso |
|-----|---------|-----|
| Energía Total | Σ(kWh eléctricos + kWh térmicos) | Dashboard |
| IDES | Energía_Total / Producción_Total | Desempeño energético |
| Emisiones | Σ(factor_emisión × cantidad) | Huella de carbono |
| Costo Normalizado | Costo_Total / Energía_Total | Comparativas |

---

## Tecnologías Frontend

- **Framework CSS:** Bootstrap 5.3.0 (CDN)
- **Iconos:** Bootstrap Icons 1.11.0
- **Gráficas:** Chart.js (dona, barras)
- **Fuente:** Inter (Google Fonts)
- **Templates:** Jinja2 (Django Template Language)
- **JavaScript:** Mínimo, solo Chart.js y Bootstrap

**Paleta de colores:**
```css
--sidebar-bg: #0f172a;        /* Azul oscuro */
--sidebar-active: #38bdf8;    /* Cyan */
--primary-brand: #0284c7;     /* Azul */
--body-bg: #f1f5f9;           /* Gris claro */
```

---

## Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Shell interactivo
python manage.py shell

# Colectar estáticos (producción)
python manage.py collectstatic

# Ejecutar servidor de desarrollo
python manage.py runserver

# Admin Django: http://localhost:8000/admin/
```

---

## Notas de Desarrollo

### Al modificar modelos
1. Hacer `makemigrations` para la app afectada
2. Revisar la migración generada
3. Aplicar con `migrate`

### Al agregar vistas
1. Aplicar decorador de seguridad apropiado (`@login_required`, `@acceso_staff`, etc.)
2. Usar `verificar_acceso_proyecto()` si es operación sobre proyecto
3. Pasar `user=request.user` a formularios que requieran validación jerárquica

### Al agregar fuentes energéticas
1. Crear modelo heredando de `CombustibleBase` o `FuenteEnergiaBase`
2. Crear formulario heredando de `RegistroEnergiaForm`
3. Agregar entrada en `FORM_MAPPING` (gestion/views.py)
4. Agregar lógica de agregación en dashboards

### Formularios con números
- Usar `RegistroEnergiaForm` como base (intercepta comas automáticamente)
- Campos numéricos usan TextInput para permitir formato visual
