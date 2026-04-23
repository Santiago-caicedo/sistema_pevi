# Sistema de Diseño - PEVI Colombia

Documentación completa del sistema visual, componentes, paletas de color, tipografía, gráficos, tarjetas, animaciones y patrones de diseño utilizados en la plataforma PEVI Colombia.

**Stack Frontend:** Bootstrap 5.3.0 + Chart.js 4.4.1 + Anime.js 3.2.2 + Leaflet + Google Fonts (Inter, Work Sans)

**Nota:** Todo el CSS y JavaScript es inline dentro de los templates Django. No existen archivos `.css` ni `.js` separados en `/static/`. Los estilos se definen en bloques `<style>` y los scripts en bloques `<script>` dentro de cada template.

---

## Tabla de Contenidos

1. [Tokens de Diseño](#1-tokens-de-diseño)
2. [Tipografía](#2-tipografía)
3. [Sistema de Sombras](#3-sistema-de-sombras)
4. [Border Radius](#4-border-radius)
5. [Layouts Base](#5-layouts-base)
6. [Tarjetas (Cards)](#6-tarjetas-cards)
7. [Tarjetas KPI](#7-tarjetas-kpi)
8. [Tablas](#8-tablas)
9. [Badges y Estados](#9-badges-y-estados)
10. [Botones](#10-botones)
11. [Formularios](#11-formularios)
12. [Modales](#12-modales)
13. [Gráficos Chart.js](#13-gráficos-chartjs)
14. [Hero Sections](#14-hero-sections)
15. [Glassmorphism y Efectos Decorativos](#15-glassmorphism-y-efectos-decorativos)
16. [Animaciones](#16-animaciones)
17. [Mapa Interactivo](#17-mapa-interactivo)
18. [PDF / Informe Impreso](#18-pdf--informe-impreso)
19. [Página de Login](#19-página-de-login)
20. [Sitio Público vs App Interna](#20-sitio-público-vs-app-interna)
21. [Responsive](#21-responsive)
22. [Iconografía](#22-iconografía)

---

## 1. Tokens de Diseño

### 1.1 Variables CSS - App Interna (`base.html`)

```css
:root {
    --sidebar-bg: #0f172a;
    --sidebar-text: #94a3b8;
    --sidebar-active: #38bdf8;
    --sidebar-active-bg: rgba(56, 189, 248, 0.1);
    --body-bg: #f1f5f9;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --primary-brand: #0284c7;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
```

### 1.2 Variables CSS - Sitio Público (`base_public.html`)

```css
:root {
    --govco-blue: #3366cc;
    --upme-green: #4caf50;
    --upme-blue: #2962ff;
    --text-dark: #333333;
    --text-gray: #666666;
}
```

### 1.3 Variables CSS - Login (`login.html`)

```css
:root {
    --background: #0f172a;
    --foreground: #111827;
    --muted-foreground: #6b7280;
    --border: #e5e7eb;
    --card: #ffffff;
    --radius: 0.9rem;
}
```

### 1.4 Paleta Completa de Colores

| Grupo | Color | Hex | Uso |
|-------|-------|-----|-----|
| **Primarios** | Sky 600 | `#0284c7` | Brand principal, botones, links |
| | Sky 400 | `#38bdf8` | Sidebar activo, acentos luminosos |
| | Sky 500 | `#0ea5e9` | Botones portal, highlights |
| | Sky 700 | `#0369a1` | Hover de botones primarios |
| **Oscuros** | Slate 900 | `#0f172a` | Sidebar, fondos hero, cover PDF |
| | Slate 800 | `#1e293b` | Fondos secundarios oscuros |
| | Slate 700 | `#334155` | Gradientes hero |
| | Gray 900 | `#111827` | Texto principal login, botón login |
| **Neutros** | Slate 100 | `#f1f5f9` | Fondo body app interna |
| | Slate 50 | `#f8fafc` | Fondos thead, alternancia filas |
| | Gray 50 | `#f9fafb` | Fondos inputs, hover filas |
| | White | `#ffffff` | Tarjetas, fondos |
| **Texto** | Slate 800 | `#1e293b` | Texto primario app |
| | Slate 500 | `#64748b` | Texto secundario/muted |
| | Gray 500 | `#6b7280` | Labels, subtítulos |
| | Gray 400 | `#9ca3af` | Placeholders, meta text |
| **Semánticos** | Green 500 | `#22c55e` | Éxito, finalizado, ahorros |
| | Green 600 | `#16a34a` | Hover verde |
| | Emerald 600 | `#059669` | Íconos verdes |
| | Yellow 500 | `#ffc107` | Warning, electricidad en gráficos |
| | Amber 500 | `#f59e0b` | KPI warning, costos |
| | Red 500 | `#dc3545` | Danger, térmico en gráficos |
| | Red 600 | `#ef4444` | Alertas error |
| | Cyan 600 | `#0891b2` | Info badges |
| | Blue 700 | `#1d4ed8` | Chips, badges soft-primary |
| **Gubernamental** | Gov Blue | `#3366cc` | Barra Gov.co |
| | UPME Green | `#4caf50` | Nav activo público |
| | UPME Blue | `#2962ff` | Acento navbar público |
| **Bandera** | Amarillo | `#fdd835` | Bandera colombiana |
| | Azul | `#1565c0` | Bandera colombiana |
| | Rojo | `#c62828` | Bandera colombiana |

### 1.5 Colores Soft (Fondos con opacidad)

```css
.bg-soft-success    { background-color: #dcfce7; color: #166534; }
.bg-soft-warning    { background-color: #fef3c7; color: #92400e; }
.bg-soft-primary    { background-color: #e0f2fe; color: #075985; }
.bg-soft-danger     { background-color: #fee2e2; color: #991b1b; }
.bg-soft-info       { background-color: #cffafe; color: #0891b2; }
.bg-soft-secondary  { background-color: #f1f5f9; color: #475569; }
```

### 1.6 Chips (Dashboard Nacional)

```css
.chip-soft-primary  { background: rgba(37,99,235,.06); border-color: rgba(37,99,235,.25); color: #1d4ed8; }
.chip-soft-warning  { background: rgba(245,158,11,.06); border-color: rgba(245,158,11,.25); color: #92400e; }
.chip-soft-info     { background: rgba(6,182,212,.06);  border-color: rgba(6,182,212,.25);  color: #0e7490; }
```

### 1.7 Gradientes Recurrentes

| Nombre | CSS | Uso |
|--------|-----|-----|
| Hero Oscuro | `linear-gradient(135deg, #0f172a 0%, #334155 100%)` | Hero centros, nosotros |
| Hero Resultados | `linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #0369a1 70%, #0284c7 100%)` | Hero resultados |
| CTA | `linear-gradient(135deg, #0f172a 0%, #0284c7 100%)` | Secciones call-to-action |
| Cover PDF | `linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%)` | Portada informe PDF |
| Footer | `linear-gradient(135deg, #0f172a 0%, #1e293b 100%)` | Footer público |
| Footer Línea | `linear-gradient(90deg, #0ea5e9, #22c55e, #0ea5e9)` | Línea decorativa top footer |
| Login Fondo | `linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)` | Fondo página login |
| KPI Dark | `radial-gradient(circle at top left, #1f2937 0, #020617 60%)` | KPI oscuro dashboard nacional |
| Filtro Nacional | `radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%)` | Card filtro dashboard nacional |
| Navbar Gov.co | `linear-gradient(90deg, #3366cc 0%, #1a4a9e 100%)` | Barra gobierno |
| Icono Primario | `linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%)` | Íconos en cards KPI home |
| Icono Verde | `linear-gradient(135deg, #059669 0%, #10b981 100%)` | Íconos verdes en home |
| Icono Amber | `linear-gradient(135deg, #d97706 0%, #f59e0b 100%)` | Íconos warning en home |
| Savings | `linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)` | Sección ahorros proyecto |
| Texto Gradiente | `linear-gradient(135deg, #38bdf8 0%, #22d3ee 50%, #34d399 100%)` | Título hero resultados |

---

## 2. Tipografía

### 2.1 Fuentes

| Contexto | Familia | Pesos | Import |
|----------|---------|-------|--------|
| App Interna | `'Inter', sans-serif` | 300, 400, 500, 600, 700 | Google Fonts |
| Sitio Público | `'Work Sans', sans-serif` | 300, 400, 500, 600, 700 | Google Fonts |
| Login | `'Inter', system-ui, -apple-system, BlinkMacSystemFont` | 500, 600 | Google Fonts |
| PDF | `'Inter', sans-serif` | 300, 400, 600, 700 | Inline |
| Monospace (datos) | `font-monospace` (Bootstrap) | - | Sistema |

### 2.2 Escala Tipográfica

| Elemento | Tamaño | Peso | Color | Tracking |
|----------|--------|------|-------|----------|
| Título página (`.page-title`) | 1.5rem | 700 | `--text-primary` | - |
| H2 KPI (dashboard) | `<h2>` | 700 (bold) | white / dark | - |
| H4 KPI (estratégico) | `<h4>` | 700 | primary / dark | - |
| Valor KPI Nacional | 1.4rem | 800 | dark | - |
| Unidad KPI | 0.75rem | - | `#9ca3af` | uppercase |
| Label KPI | 0.75rem | - | `#6b7280` | uppercase, 0.16em |
| Tabla header | 0.75-0.85rem | 600 | `--text-secondary` | uppercase, 0.14em |
| Tabla body | 0.86rem | 400 | `--text-primary` | - |
| Sidebar heading | 0.75rem | 600 | `#475569` | uppercase, 1px |
| Badge | 0.65-0.75em | 500-600 | Varía | - |
| Small labels | 0.7rem | 600 (bold) | `text-muted` | uppercase |
| Body base | 0.95rem | 400 | `--text-primary` | - |
| Hero H1 (home) | 3.5rem (desktop) / 2.2rem (mobile) | 800 | white | -1px |
| Hero H1 (resultados) | `display-3` (~3rem) | 700 | white | - |
| Hero H1 (centros/nosotros) | `display-4` (~2.5rem) | 700 | white | - |
| Login título | 1.7rem | 600 | dark | -0.02em |
| Login subtítulo | 0.92rem | 400 | `#6b7280` | - |
| PDF título portada | 32pt | 700 | white | - |
| PDF subtítulo | 11pt | - | `#38bdf8` | uppercase, 3px |
| PDF tabla | 9pt | 400 | dark | - |
| PDF tabla header | 8pt | - | white | uppercase, 0.5px |

---

## 3. Sistema de Sombras

| Token | CSS | Uso |
|-------|-----|-----|
| `--shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Cards por defecto |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | Hover lift |
| Shadow navbar | `0 2px 8px rgba(0, 0, 0, 0.1)` | Navbar público |
| Shadow dropdown | `0 4px 20px rgba(0,0,0,0.15)` | Menú dropdown |
| Shadow KPI Nacional | `0 10px 25px rgba(15,23,42,.04)` | KPI cards |
| Shadow KPI Dark | `0 18px 40px rgba(15,23,42,.55)` | KPI oscuro |
| Shadow Login Shell | `0 40px 80px rgba(0,0,0,0.4), 0 20px 40px rgba(0,0,0,0.3)` | Contenedor login |
| Shadow btn portal | `0 6px 16px rgba(14,165,233,0.45)` | Botón ingresar |
| Shadow btn login | `0 14px 30px rgba(15,23,42,0.22)` | Botón iniciar sesión |
| Shadow glassmorphism | `0 30px 60px rgba(0,0,0,0.3)` | Stat cards resultados |
| Shadow news hover | `0 15px 30px rgba(0, 0, 0, 0.1)` | Cards noticias hover |
| Shadow Leaflet popup | `0 10px 30px rgba(0,0,0,0.15)` | Popups mapa |

---

## 4. Border Radius

| Valor | Uso |
|-------|-----|
| `2px` | Íconos Gov.co |
| `4px` | Nav links público |
| `6px` | Nav links sidebar |
| `8px` | Dropdowns, border-radius Chart.js bars |
| `10px` | KPI PDF, info boxes PDF |
| `12px` | `.card-modern`, cards centros, filtro resultados |
| `16px` | Cards noticias, stat mini resultados |
| `20px` | Filtro resultados, tags filtro |
| `24px` | Stat cards resultados (glassmorphism) |
| `28px` | Shell login |
| `50rem` / `999px` | Badges pill, botones pill, chips |
| `50%` | Avatares, íconos circulares, social buttons |
| `1rem` | KPI Nacional, card-panel |
| `1.25rem` | Card filtro dashboard nacional |

---

## 5. Layouts Base

### 5.1 App Interna (`base.html`)

```
┌──────────────────────────────────────────────────┐
│ SIDEBAR (260px fijo)  │  MAIN CONTENT            │
│                       │  ┌─────────────────────┐  │
│  Logo PEVI            │  │ Top Navbar           │  │
│  ─────────            │  │ (breadcrumbs + user) │  │
│  NAVEGACIÓN           │  ├─────────────────────┤  │
│  ├─ Dashboard         │  │                     │  │
│  ├─ Proyectos         │  │  CONTENIDO          │  │
│  ├─ Empresas          │  │  (padding: 2rem)    │  │
│  ├─ Equipo            │  │                     │  │
│  ├─ MÉTRICAS          │  │                     │  │
│  │  ├─ Estratégico    │  │                     │  │
│  │  └─ Nacional       │  │                     │  │
│  └─ SUPERADMIN        │  │                     │  │
│     └─ Control Panel  │  │                     │  │
│                       │  └─────────────────────┘  │
│  Mensajes (alerts)    │                           │
└──────────────────────────────────────────────────┘
```

**Sidebar:**
- Fondo: `#0f172a` (slate-900)
- Ancho: 260px fijo
- Posición: fixed, z-index 1000
- Nav links: padding 0.75rem 1.5rem, border-radius 6px
- Activo: color `#38bdf8`, fondo `rgba(56, 189, 248, 0.1)`
- Hover: color white, fondo `rgba(255,255,255,0.05)`
- Headings de sección: 0.75rem uppercase, letter-spacing 1px, color `#475569`

**Main Content:**
- Margin-left: 260px
- Padding: 2rem
- Fondo: `#f1f5f9`

**Top Navbar:**
- Background: transparent
- Flex: justify-content space-between
- Contiene: título de página + perfil de usuario

**Menú por Rol:**
- Estudiante: Dashboard, Proyectos
- Profesor: + Empresas, Equipo (parcial)
- Director Centro: + Equipo completo, Métricas Estratégico
- Director Nacional: + Métricas Nacional
- Superadmin: + Control Panel

### 5.2 Sitio Público (`base_public.html`)

```
┌──────────────────────────────────────────────────┐
│ BARRA GOV.CO (36px, gradiente azul)              │
├──────────────────────────────────────────────────┤
│ NAVBAR PEVI (blanca, border-bottom 3px azul)     │
│ Logo PEVI | Navegación | Logos | Btn Ingresar    │
├──────────────────────────────────────────────────┤
│                                                  │
│              CONTENIDO DE PÁGINA                 │
│              (padding-top: 110px)                │
│                                                  │
├──────────────────────────────────────────────────┤
│ FOOTER (gradiente oscuro)                        │
│ ┌────────┬────────┬────────┬────────┐            │
│ │ Brand  │ Nav    │ Recursos│ Contacto│           │
│ └────────┴────────┴────────┴────────┘            │
│ ─── Línea gradiente (sky → green → sky) ───      │
│ Copyright | Legal | Privacidad                   │
└──────────────────────────────────────────────────┘
```

**Barra Gov.co:**
- Gradiente: `#3366cc → #1a4a9e`
- Altura: 36px
- Links blancos con íconos

**Navbar PEVI:**
- Fondo blanco, sombra `0 2px 8px rgba(0,0,0,0.1)`
- Border-bottom: 3px solid `#2962ff`
- Logo: 55px altura con bandiera colombiana decorativa
- Nav links: 14px, peso 500, hover azul `#2962ff`
- Activo: fondo verde `#4caf50`, texto blanco, border-radius 4px
- Botón portal: pill, fondo `#0ea5e9`, sombra cyan

**Footer:**
- Gradiente: `#0f172a → #1e293b`
- Línea decorativa top: gradiente `#0ea5e9 → #22c55e → #0ea5e9` (4px)
- 4 columnas: Brand, Navegación, Recursos, Contacto
- Títulos: 13px uppercase, underline decorativa `#0ea5e9` (30px)
- Links: color `#94a3b8`, hover `#0ea5e9` con slide-in de ícono
- Social buttons: 40px circulares, hover `#0ea5e9` + translateY(-3px)
- Logos partners: grayscale(100%) → grayscale(0%) on hover

---

## 6. Tarjetas (Cards)

### 6.1 Card Modern (Base)

```css
.card-modern {
    background: #ffffff;
    border: none;
    border-radius: 12px;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    transition: transform 0.2s, box-shadow 0.2s;
}
```

Uso: Todas las tarjetas de la app interna (dashboard, detalle, listas, métricas).

### 6.2 Card con Hover Lift

```css
.hover-lift {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.hover-lift:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
```

Uso: Cards interactivas en dashboard, cards de energía en proyecto_detalle, cards en sitio público.

### 6.3 Cards de Energía (proyecto_detalle)

Seis tarjetas con código de color por tipo de energético:

| Energético | Badge Color | Ícono | Border-start | Bootstrap Icon |
|------------|-------------|-------|--------------|----------------|
| Electricidad | `bg-soft-warning text-warning` | `bi-plug-fill` | `border-warning` | Amarillo |
| Gas Natural | `bg-soft-primary text-primary` | `bi-fire` | `border-primary` | Azul |
| Carbón Mineral | `bg-dark text-white` | `bi-box-seam-fill` | `border-dark` | Negro |
| Fuel Oil | `bg-soft-danger text-danger` | `bi-droplet-fill` | `border-danger` | Rojo |
| Biomasa | `bg-soft-success text-success` | `bi-recycle` | `border-success` | Verde |
| Gas Propano | `bg-soft-info text-info` | `bi-cloud-fog2-fill` | `border-info` | Cyan |

**Estructura HTML:**
```html
<div class="card-modern h-100 p-4 position-relative hover-lift bg-white">
    <!-- Header: Título + Badge tipo + Ícono circular -->
    <div class="d-flex justify-content-between align-items-start mb-3">
        <div>
            <h6 class="fw-bold text-dark mb-1">Título</h6>
            <span class="badge bg-soft-{color} text-{color} border">Tipo</span>
        </div>
        <div class="rounded-circle bg-soft-{color} text-{color} p-2 d-flex"
             style="width: 40px; height: 40px;">
            <i class="bi bi-{icon} fs-5"></i>
        </div>
    </div>
    <!-- Datos con border-start coloreado -->
    <div class="border-start border-2 border-{color} ps-3">
        <small class="text-muted">Label</small>
        <div class="fw-bold small">Valor</div>
    </div>
    <!-- Botones de acción -->
    <div class="mt-3 d-flex gap-2">
        <a class="btn btn-light btn-sm border text-secondary fw-medium">Ver</a>
        <a class="btn btn-outline-{color} btn-sm border-dashed fw-medium">Registrar</a>
    </div>
</div>
```

### 6.4 Cards de Noticias (home)

```css
/* Card */
border-radius: 16px;
border: none;
overflow: hidden;
transition: transform 0.3s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.3s ease;

/* Hover */
transform: translateY(-8px);
box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);

/* Imagen */
height: 220px;
object-fit: cover;
transition: transform 0.6s cubic-bezier(0.33, 1, 0.68, 1);
/* Hover: scale(1.08) */

/* Badge fecha (glassmorphism) */
background: rgba(255, 255, 255, 0.95);
border-radius: 10px;
box-shadow: 0 4px 10px rgba(0,0,0,0.1);
backdrop-filter: blur(4px);

/* Underline animado en título */
background-image: linear-gradient(to right, #0284c7, #0284c7);
background-size: 0% 2px;  /* → 100% 2px on hover */
background-position: left bottom;
transition: background-size 0.3s ease;
```

### 6.5 Cards de Centros (centros.html)

```css
/* Card */
border-radius: 12px;
box-shadow: shadow-sm;
transition: transform 0.3s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.3s ease;
/* Hover: translateY(-8px), box-shadow 0 15px 30px rgba(0,0,0,0.1) */

/* Header imagen: 160px altura */
/* Logo flotante: 70px circular, border 3px white, box-shadow, mb-n4 (overlap) */
/* Gradiente fallback: linear-gradient(135deg, {color_primario} 0%, #0f172a 100%) */
```

### 6.6 Cards de Biblioteca (documento)

```css
/* Layout: row g-0 con col-4 (imagen) + col-8 (contenido) */
/* Imagen: rotate(-3deg) translateX(5px), hover: rotate(0deg) scale(1.05) */
/* Título: line-height 1.4 */
/* Descripción: line-clamp-3 */
```

### 6.7 Card Panel (Dashboard Nacional)

```css
.card-panel {
    border-radius: 1rem;
    border: 1px solid rgba(226,232,240,1);
    padding: 1rem 1.2rem 1.2rem;
    background: #ffffff;
}
.card-panel-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: .75rem;
}
.card-panel-title {
    font-size: .85rem;
    text-transform: uppercase;
    letter-spacing: .14em;
    color: #0f172a;
}
```

### 6.8 Card Filter (Dashboard Nacional)

```css
.card-filter {
    background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%);
    color: #fff;
    border-radius: 1.25rem;
    padding: 1.75rem;
    position: relative;
    overflow: hidden;
}
/* Decoración: radial-gradient cyan en esquina inferior derecha */
.card-filter::after {
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(56,189,248,.25), transparent 70%);
}
```

---

## 7. Tarjetas KPI

### 7.1 KPI Dashboard Principal

**4 variantes en grid `col-md-3`:**

| Variante | Clases | Icono | Fondo |
|----------|--------|-------|-------|
| Primario | `bg-primary text-white` | `bi-folder2-open` (5rem, opacity-25) | Azul sólido |
| Warning border | `bg-white border-start border-4 border-warning` | - | Blanco con borde izquierdo |
| Info border | `bg-white border-start border-4 border-info` | - | Blanco con borde izquierdo |
| Dark interactivo | `bg-dark text-white hover-lift` | `bi-globe-americas` / `bi-graph-up-arrow` | Negro con cursor pointer |

**Estructura primario:**
```html
<div class="card-modern bg-primary text-white p-4 position-relative overflow-hidden">
    <div class="position-relative z-1">
        <h2 class="fw-bold mb-0">{{ valor }}</h2>
        <small class="text-white-50 text-uppercase fw-bold ls-1">Label</small>
    </div>
    <i class="bi bi-folder2-open position-absolute end-0 bottom-0 mb-n2 me-2"
       style="font-size: 5rem; opacity: .25;"></i>
</div>
```

### 7.2 KPI Proyecto Detalle

**3 cards con `border-start border-4`:**

| Card | Border | Ícono | Métrica |
|------|--------|-------|---------|
| Consumo Total | `border-primary` | `bi-lightning-charge-fill` (bg-soft-primary) | kWh con split eléctrico/térmico |
| Huella Carbono | `border-success` | `bi-globe-americas` (bg-soft-success) | TonCO2eq/año |
| Costo Operativo | `border-warning` | `bi-currency-dollar` (bg-soft-warning) | $ COP/año |

Cada card tiene sub-métricas:
```html
<!-- Split eléctrico vs térmico -->
<div class="d-flex gap-3 mt-2">
    <div class="border-start border-2 border-warning ps-2">
        <i class="bi bi-plug-fill text-warning"></i>
        <small class="text-muted">Eléctrica</small>
        <div class="fw-bold small">{{ valor }} kWh</div>
    </div>
    <div class="border-start border-2 border-danger ps-2">
        <i class="bi bi-fire text-danger"></i>
        <small class="text-muted">Térmica</small>
        <div class="fw-bold small">{{ valor }} kWh</div>
    </div>
</div>
```

### 7.3 KPI Dashboard Estratégico

**4 cards con `border-start border-4`:**

| Card | Border | Valor Style | Unidad |
|------|--------|-------------|--------|
| Proyectos | `border-dark` | `<h3>` dark | - |
| Energía | `border-primary` | `<h4>` primary | `<span class="fs-6 text-muted">kWh</span>` |
| Costos | `border-warning` | `<h4>` dark | Formato moneda |
| Emisiones | `border-success` | `<h4>` success | `<span class="fs-6">Ton</span>` |

### 7.4 KPI Dashboard Nacional

**Sistema de KPI más elaborado:**

```css
.kpi-card {
    border-radius: 1rem;
    padding: 1.1rem 1.2rem;
    display: flex;
    gap: 1rem;
    align-items: center;
    box-shadow: 0 10px 25px rgba(15,23,42,.04);
    border: 1px solid rgba(226,232,240,.9);
    background: #fff;
}
.kpi-icon {
    width: 44px; height: 44px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center; justify-content: center;
    background: rgba(15,23,42,.04);
    font-size: 1.3rem;
}
.kpi-value { font-size: 1.4rem; font-weight: 800; }
.kpi-unit  { font-size: 0.75rem; text-transform: uppercase; color: #9ca3af; }
.kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: .16em; color: #6b7280; }
```

**Variantes:**
- `kpi-neutral` — Fondo blanco estándar
- `kpi-primary` — Border-left 4px `#0ea5e9`
- `kpi-warning` — Border-left 4px `#f59e0b`
- `kpi-success` — Border-left 4px `#22c55e`
- `kpi-dark` — Gradiente oscuro, texto blanco, sombra fuerte
- `kpi-primary-light` — Border-left + gradiente `#eff6ff → #ffffff`
- `kpi-success-light` — Border-left + gradiente `#ecfdf5 → #ffffff`

### 7.5 KPI Home (Stat Widgets)

```css
/* Contenedor con margin-top negativo para solapar hero */
margin-top: -100px;
z-index: 20;

/* Card */
background: white;
border-radius: 1rem;
border-left: 5px solid {color};
box-shadow: shadow-lg;
transition: transform 0.3s ease, box-shadow 0.3s ease;
/* Hover: translateY(-10px) */

/* Ícono box */
width: 60px; height: 60px;
border-radius: 0.75rem;
background: linear-gradient(135deg, {color1} 0%, {color2} 100%);
box-shadow: shadow-sm;
/* Hover: scale(1.1) rotate(5deg) */

/* Ícono background decorativo */
opacity: 0.1;
font-size: 5rem;
transform: rotate(-15deg);
position: absolute; right; bottom;
```

### 7.6 KPI Resultados (Glassmorphism)

**Cards principales:**
```css
background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.05) 100%);
backdrop-filter: blur(20px);
border: 1px solid rgba(255,255,255,0.15);
border-radius: 24px;
/* Hover: translateY(-8px), box-shadow 0 30px 60px rgba(0,0,0,0.3) */

.stat-icon-lg    { width: 70px; height: 70px; border-radius: 20px; }
.stat-number-lg  { font-size: 3.5rem; font-weight: 800; letter-spacing: -2px; }
.stat-unit       { font-size: 1.25rem; color: rgba(255,255,255,0.7); }
.stat-label      { font-size: 0.9rem; color: rgba(255,255,255,0.6); }
```

**Cards mini:**
```css
background: rgba(255,255,255,0.08);
backdrop-filter: blur(10px);
border: 1px solid rgba(255,255,255,0.1);
border-radius: 16px;
/* Hover: background rgba(255,255,255,0.12), translateY(-4px) */

.stat-mini-number { font-size: 2rem; font-weight: 700; }
.stat-mini-label  { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
```

---

## 8. Tablas

### 8.1 Table Modern (Base)

```css
.table-modern {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}
.table-modern thead th {
    background-color: #f8fafc;
    color: var(--text-secondary);   /* #64748b */
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
}
.table-modern tbody td {
    padding: 1rem;
    vertical-align: middle;
    border-bottom: 1px solid #f1f5f9;
    color: var(--text-primary);
}
.table-modern tr:last-child td {
    border-bottom: none;
}
/* Hover row (via .table-hover) */
.table-modern tbody tr:hover {
    background-color: #f9fafb;
}
```

### 8.2 Variante Dashboard Nacional

```css
.table-modern thead {
    background: #f9fafb;
    border-bottom: 1px solid rgba(226,232,240,1);
}
.table-modern thead th {
    font-size: .75rem;
    letter-spacing: .14em;
    color: #6b7280;
    padding-top: .75rem;
    padding-bottom: .7rem;
}
.table-modern tbody td {
    font-size: .86rem;
    padding-top: .7rem;
    padding-bottom: .7rem;
}
```

### 8.3 Tabla de Proyectos (lista_proyectos)

| Columna | Diseño |
|---------|--------|
| Proyecto/Cliente | Ícono `rounded-3 bg-soft-primary` 40x40px + nombre truncado (max-width 250px) + subtítulo empresa |
| Líder & Equipo | Ícono `bi-star-fill` (si es el usuario actual) + badge equipo `rounded-pill` |
| Centro | Badge `bg-light text-dark border` (solo vista nacional) |
| Estado | Badge coloreado + fase badge `bg-dark text-white` |
| Acciones | `btn btn-light btn-sm border` |

### 8.4 Tabla de Usuarios (lista_usuarios)

| Columna | Diseño |
|---------|--------|
| Usuario | Avatar circular 40px `bg-secondary text-white` con iniciales + nombre + email |
| Rol/Cargo | Badge por rol (ver sección Badges) + subtítulo cargo |
| Estado | Badge `bg-soft-success` (Activo) o `bg-soft-danger` (Inactivo) |
| Último Acceso | Fecha o "Nunca" |
| Acciones | Dropdown `btn-light rounded-circle` con three-dots |

### 8.5 Tabla de Reducción (proyecto_detalle)

| Columna | Diseño |
|---------|--------|
| Energético | Ícono circular 36px coloreado + nombre |
| Consumo Actual | Valor centrado con unidad |
| Costo Actual | Valor centrado en COP |
| % Reducción | Badge: `bg-success` si >0, `bg-secondary` si 0, `rounded-pill px-3 py-2 fs-6` |
| Ahorro Energía | `text-success fw-bold` |
| Ahorro Costo | `text-success fw-bold` |
| CO2 Evitado | `text-success fw-bold` |
| Acciones | `btn btn-sm btn-light border` con `bi-pencil` |

### 8.6 Tabla OPM (Oportunidades de Mejora)

10+ columnas con footer de totales calculado por JavaScript:
- Código, Descripción, Energético, Ahorro Energía, Costos Evitados, Emisiones Evitadas, Inversión, VPN, TIR, Payback, Observaciones, Acciones
- Footer: sumas con `toLocaleString('es-CO')`
- Acciones: botones editar/eliminar

### 8.7 Card Table (Dashboard Nacional)

```css
.card-table {
    border-radius: 1rem;
    border: 1px solid rgba(226,232,240,1);
    overflow: hidden;
    background: #ffffff;
}
.card-table-header {
    padding: 1rem 1.3rem;
    border-bottom: 1px solid rgba(226,232,240,1);
    background: linear-gradient(90deg, #f9fafb 0, #ffffff 60%);
}
```

---

## 9. Badges y Estados

### 9.1 Estados de Proyecto

| Estado | Clases | Ícono |
|--------|--------|-------|
| En Ejecución | `badge rounded-pill bg-soft-primary text-primary border border-primary px-3 py-2` | Spinner `spinner-grow spinner-grow-sm` (0.5rem) |
| En Revisión | `badge rounded-pill bg-soft-warning text-warning border border-warning px-3 py-2` | `bi-eye-fill` |
| Finalizado | `badge rounded-pill bg-soft-success text-success border border-success px-3 py-2` | `bi-check-circle-fill` |
| Borrador | `badge rounded-pill bg-soft-secondary text-secondary border px-3 py-2` | `bi-pencil` |

### 9.2 Badge de Fase

```html
<span class="badge rounded-pill bg-dark text-white px-3 py-2">
    <i class="bi bi-flag-fill me-1"></i> {{ fase }}
</span>
```

### 9.3 Roles de Usuario

| Rol | Clases |
|-----|--------|
| Director Nacional | `bg-dark text-white border` |
| Director Centro | `bg-soft-primary text-primary border border-primary-subtle` |
| Profesor | `bg-soft-info text-info border border-info-subtle` |
| Estudiante | `bg-light text-secondary border border-secondary-subtle` |

### 9.4 Badge Soft (Dashboard Nacional)

```css
.badge-soft-secondary {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    color: #4b5563;
    font-weight: 500;
    font-size: .75rem;
    border-radius: 999px;
    padding: .22rem .7rem;
}
.badge-soft-primary {
    background: #eff6ff;
    border: 1px solid #dbeafe;
    color: #1d4ed8;
    font-weight: 600;
}
```

### 9.5 Badge Porcentaje Reducción

```html
<!-- Si > 0% -->
<span class="badge bg-success rounded-pill px-3 py-2 fs-6">{{ valor }}%</span>
<!-- Si = 0% -->
<span class="badge bg-secondary rounded-pill px-3 py-2 fs-6">0%</span>
```

### 9.6 Estado Activo/Inactivo (usuarios)

```html
<!-- Activo -->
<span class="badge bg-soft-success text-success rounded-pill border border-success-subtle px-2">Activo</span>
<!-- Inactivo -->
<span class="badge bg-soft-danger text-danger rounded-pill border border-danger-subtle px-2">Inactivo</span>
```

---

## 10. Botones

### 10.1 Botones Principales

| Variante | Clases | Uso |
|----------|--------|-----|
| Primario | `btn btn-primary px-5 py-2 shadow-sm fw-bold` | Guardar formularios |
| Primario pill | `btn btn-primary btn-sm rounded-pill shadow-sm fw-medium` | Crear nuevo (listas) |
| Secundario | `btn btn-light border px-4` | Cancelar |
| Dark | `btn btn-dark btn-sm fw-medium shadow-sm` | Generar PDF |
| Success | `btn btn-success btn-sm fw-bold shadow-sm` | Finalizar proyecto |
| Outline | `btn btn-outline-primary border-dashed fw-medium` | Registrar (cards energía) |
| Outline dark pill | `btn btn-outline-dark rounded-pill w-100 fw-medium` | Ver detalle centro |
| Light circle | `btn btn-light btn-sm border rounded-circle shadow-sm` | Dropdown tres puntos |

### 10.2 Botón Portal (Público)

```css
.btn-portal {
    padding: 0.45rem 1.4rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border: 2px solid #0ea5e9;
    background: #0ea5e9;
    color: #ffffff;
    box-shadow: 0 6px 16px rgba(14,165,233,0.45);
}
.btn-portal:hover {
    background: #0369a1;
    box-shadow: 0 10px 22px rgba(3,105,161,0.55);
    transform: translateY(-1px);
}
```

### 10.3 Botones Hero (Home)

```css
.btn-hero {
    padding: 0.8rem 2.5rem;
    border-radius: 50rem;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: all 0.3s ease;
}
/* Primario: bg #0284c7, hover: #0369a1, translateY(-3px) */
/* Outline: border white, hover: bg white, color #0f172a */
```

### 10.4 Botón Login

```css
.btn-primary-login {
    width: 100%;
    padding: 0.95rem 1rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-radius: 999px;
    background: #111827;
    color: #f9fafb;
    box-shadow: 0 14px 30px rgba(15,23,42,0.22);
}
/* Active: scale(0.98), shadow reducido */
```

### 10.5 Botón Reset Filtro (Dashboard Nacional)

```css
.btn-reset-filter {
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,.5);
    background-color: rgba(15,23,42,.9);
    color: #e5e7eb;
    padding: 0.65rem 1.25rem;
    font-weight: 500;
}
.btn-reset-filter:hover {
    border-color: #38bdf8;
    color: #f9fafb;
}
```

### 10.6 Botones Filtro (Centros/Biblioteca)

```css
/* Activo */
.btn.btn-dark.rounded-pill.px-4.fw-medium

/* Inactivo */
.btn.btn-white.border.shadow-sm.rounded-pill.px-4.fw-medium.text-muted
.btn-white { background: white; }
.btn-white:hover { background: #f1f5f9; }
```

---

## 11. Formularios

### 11.1 Estructura General

```html
<div class="card-modern border-0 shadow-lg">
    <!-- Header -->
    <div class="p-4 border-bottom d-flex align-items-center gap-3">
        <div class="rounded-circle bg-soft-primary p-2 text-primary">
            <i class="bi bi-{icon} fs-4"></i>
        </div>
        <div>
            <h5 class="fw-bold mb-0">Título</h5>
            <p class="text-muted small mb-0">Subtítulo</p>
        </div>
    </div>
    <!-- Body -->
    <div class="p-5">
        <!-- Secciones con headers -->
        <h6 class="text-uppercase text-primary fw-bold mb-4">
            <i class="bi bi-{icon} me-2"></i>Sección
        </h6>
        <!-- Campos -->
        <div class="row g-4 mb-5">
            <div class="col-md-6">
                <label class="form-label fw-semibold text-dark small">Campo</label>
                {{ field }}
                <span class="form-text">Ayuda</span>
            </div>
        </div>
    </div>
    <!-- Footer con botones -->
    <div class="d-flex justify-content-end gap-3 mt-5 pt-3 border-top">
        <a class="btn btn-light border px-4">Cancelar</a>
        <button class="btn btn-primary px-5 py-2 shadow-sm fw-bold">Guardar</button>
    </div>
</div>
```

### 11.2 Registro de Energía (Especial)

**Secciones con colores:**
- Info empresa: `alert alert-light border` con ícono `text-primary`
- Costos: `bg-light p-3 rounded border border-light`
- Conversión energética: `bg-soft-warning p-3 rounded border border-warning-subtle` (destacado amarillo)
- Headers: `text-uppercase text-primary fw-bold mb-3 border-bottom pb-2` con íconos

**Inputs numéricos:**
- Se renderizan como `type="text"` (no number) para formato visual
- JavaScript formatea con separadores de miles
- Campos auto-calculados en readonly con fondo amarillo claro

**Modal calculadora de unidades:**
- Header: `bg-primary text-white`
- Resultado: `bg-white p-3 rounded border text-center` con `h4 fw-bold text-success`

### 11.3 Selector de Equipo (proyecto_form)

```html
<!-- Área de seleccionados -->
<div class="d-flex flex-wrap gap-2 p-3 bg-light rounded border" style="min-height: 46px;">
    <span class="badge bg-soft-{rol_color} text-{rol_color} d-inline-flex align-items-center gap-1 px-2 py-1">
        <i class="bi bi-{rol_icon}"></i> Nombre
        <button class="btn-close btn-close-sm"></button>
    </span>
</div>

<!-- Pills de rol -->
<div class="d-flex flex-wrap gap-2">
    <button class="btn btn-sm rounded-pill active">Todos</button>
    <button class="btn btn-sm btn-outline-{color} rounded-pill">Rol</button>
</div>

<!-- Panel de usuarios -->
<div class="border rounded p-3 bg-white" style="max-height: 220px; overflow-y: auto;">
    <div class="border rounded px-3 py-2 cursor-pointer" 
         onclick="..." 
         style="transition: all 0.15s ease;">
        <!-- Selected: background #e8f4fd, border-color #0284c7 -->
    </div>
</div>
```

**Colores por rol:**
- ESTUDIANTE → primary (azul)
- PROFESOR → success (verde)
- DIRECTOR_CENTRO → warning (amarillo)
- DIRECTOR_NACIONAL → danger (rojo)

### 11.4 Inputs Login

```css
.form-input {
    padding: 0.9rem 1rem;
    font-size: 0.95rem;
    border-radius: 0.75rem;
    border: 1px solid #e5e7eb;
    background: #f9fafb;
}
.form-input:focus {
    background-color: white;
    border-color: #111827;
    box-shadow: 0 0 0 3px rgba(15,23,42,0.06);
}
```

### 11.5 Select Filter (Dashboard Nacional)

```css
.filter-select {
    background-color: rgba(15,23,42,.9);
    color: #e5e7eb;
    border-color: rgba(148,163,184,.4);
}
.filter-select:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 0 0.15rem rgba(56,189,248,.4);
    background-color: #020617;
}
```

---

## 12. Modales

### 12.1 Modal Reducción (proyecto_detalle)

```
┌─ bg-success text-white ─────────────────┐
│  Editar % de Reducción                  │
├─────────────────────────────────────────┤
│  ┌──────────────────┐                   │
│  │  [input-group-lg] │ %               │
│  │  text-center      │                 │
│  │  fw-bold          │                 │
│  └──────────────────┘                   │
│  "Valor entre 0 y 100"                 │
├─ bg-light ──────────────────────────────┤
│  [Cancelar]  [Guardar btn-success px-4] │
└─────────────────────────────────────────┘

Tamaño: modal-sm, modal-dialog-centered
Content: border-0 shadow-lg
```

### 12.2 Modal OPM (proyecto_detalle)

```
┌─ bg-light ──────────────────────────────────────────┐
│  Nueva/Editar Oportunidad de Mejora                 │
├─────────────────────────────────────────────────────┤
│  Row 1: [Código col-3] [Descripción col-5] [Tipo col-4]  │
│  Row 2: [Ahorro kWh col-4] [Costos col-4] [CO2 col-4]    │
│  Row 3: [Inversión col-3] [VPN col-3] [TIR col-3] [Payback col-3] │
│  Row 4: [Observaciones col-12 textarea]             │
├─────────────────────────────────────────────────────┤
│  [Cancelar]  [Guardar btn-success px-4]             │
└─────────────────────────────────────────────────────┘

Tamaño: modal-xl
Labels: form-label fw-medium
Required: text-danger asterisco
```

### 12.3 Modal Upload Documento

```
┌─ bg-primary text-white ─────────────────┐
│  Subir Documento                        │
├─────────────────────────────────────────┤
│  Descripción: [input text]              │
│  Archivo: [input file]                  │
│  "PDF, Excel, Imágenes (Max 10MB)"      │
├─────────────────────────────────────────┤
│  [Cancelar]  [Subir btn-primary px-4]   │
└─────────────────────────────────────────┘

Tamaño: modal-dialog-centered
Content: border-0 shadow-lg
```

### 12.4 Modal Detalle Centro (centros.html)

```
┌──────────────────────────────────────────────────────────┐
│  HEADER VISUAL (220px, imagen/gradiente con overlay)     │
│  ┌─────┐                                                │
│  │Logo │  Centro Nombre + Ciudad + Año                   │
│  └─────┘  [Social links]                                 │
├──────────────────────────────────────────────────────────┤
│  COL-LG-8 (Main)           │  COL-LG-4 (Sidebar)        │
│  ┌─KPIs (4 cards)──────┐   │  ┌─Director─────────────┐  │
│  │ Proyectos │ Empresas │   │  │  [Foto circular]     │  │
│  │ Energía   │ MWh      │   │  │  Nombre + Cargo      │  │
│  └──────────────────────┘   │  │  [Contactar]         │  │
│  Descripción                │  └──────────────────────┘  │
│  Especialidades (badges)    │  Contacto (ícono + datos)  │
│  Sectores (badges)          │  Redes Sociales            │
│  ┌─Chart Pie─┐┌─Chart Bar─┐│  [Sitio Web btn-dark pill] │
│  │ Estados   ││ Evolución ││  Stats adicionales          │
│  └───────────┘└───────────┘│                             │
└──────────────────────────────────────────────────────────┘

Tamaño: modal-xl, modal-dialog-centered
Content: border-0 rounded-4 shadow-lg
Sidebar: bg-light border-start
```

---

## 13. Gráficos Chart.js

### 13.1 Configuración Global

```javascript
// Fuente
font: { family: "'Inter', sans-serif" }

// Opciones comunes
responsive: true,
maintainAspectRatio: false

// Alturas de contenedor
// Proyecto detalle: 220px
// Reducción: 250px
// Dashboard estratégico: 250px
// Dashboard nacional: 260px
// Modal centros: 180px
```

### 13.2 Gráfico Doughnut (Matriz Energética / Huella Carbono)

```javascript
{
    type: 'doughnut',
    data: {
        labels: ['Electricidad', 'Gas Natural', ...],
        datasets: [{
            data: [valores],
            backgroundColor: colores,  // Array dinámico por fuente
            borderWidth: 0,
            hoverOffset: 10
        }]
    },
    options: {
        cutout: '60%',         // En proyecto_detalle
        // cutout: '65%',      // En dashboard_estrategico
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    font: { family: "'Inter', sans-serif", size: 10 },
                    boxWidth: 12,
                    padding: 8
                }
            },
            tooltip: {
                callbacks: {
                    label: function(c) {
                        const pct = ((c.raw / total) * 100).toFixed(1);
                        return c.label + ': ' + c.raw.toLocaleString('en-US') + ' kWh (' + pct + '%)';
                    }
                }
            }
        }
    }
}
```

### 13.3 Gráfico Barras Verticales (MBTU / Costos)

```javascript
{
    type: 'bar',
    data: {
        labels: ['Energía Eléctrica', 'Energía Térmica'],
        datasets: [{
            data: valores,
            backgroundColor: ['#ffc107', '#dc3545'],  // Yellow = Eléctrica, Red = Térmica
            borderRadius: 5,
            barThickness: 40
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
            x: { grid: { display: false } }
        },
        plugins: {
            legend: { display: false }
        }
    }
}
```

### 13.4 Gráfico Barras Horizontales (Reducción por Fuente)

```javascript
{
    type: 'bar',
    data: {
        labels: fuentesLabels,
        datasets: [{
            data: fuentesValores,
            backgroundColor: [
                'rgba(34, 197, 94, 0.8)',    // Green 500
                'rgba(16, 185, 129, 0.8)',   // Emerald 500
                'rgba(5, 150, 105, 0.8)',    // Emerald 600
                'rgba(4, 120, 87, 0.8)',     // Emerald 700
                'rgba(6, 95, 70, 0.8)',      // Emerald 800
                'rgba(20, 83, 45, 0.8)'      // Green 900
            ],
            borderColor: [...],  // Mismos colores sin alpha
            borderWidth: 2,
            borderRadius: 8,
            barThickness: 35
        }]
    },
    options: {
        indexAxis: 'y',  // Horizontal
        scales: {
            x: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        if (value >= 1000000) return (value/1000000).toFixed(1) + 'M';
                        if (value >= 1000) return (value/1000).toFixed(0) + 'K';
                        return value;
                    }
                }
            },
            y: { ticks: { font: { weight: 'bold', size: 11 } } }
        },
        plugins: {
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleFont: { size: 13, weight: 'bold' },
                bodyFont: { size: 12 },
                padding: 12,
                cornerRadius: 8
            }
        }
    }
}
```

### 13.5 Gráfico Ranking (Dashboard Nacional)

```javascript
{
    type: 'bar',
    data: {
        labels: centroNames,
        datasets: [{
            data: energiaValues,
            backgroundColor: '#0284c7',
            borderRadius: 8,
            barThickness: 38
        }]
    },
    options: {
        scales: {
            y: { grid: { color: 'rgba(148, 163, 184, 0.2)' } }
        }
    }
}
```

### 13.6 Gráfico Pie (Dashboard Nacional / Centros)

```javascript
{
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: ['#0f172a', '#1e293b', '#475569', '#64748b', '#94a3b8']  // Slate greys
        }]
    },
    options: {
        plugins: {
            legend: { position: 'bottom' }
        }
    }
}
```

### 13.7 Paleta de Colores para Gráficos

**Colores primarios (resultados públicos):**
```javascript
['#0284c7', '#059669', '#d97706', '#dc2626', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
```

**Colores con transparencia:**
```javascript
['rgba(2,132,199,0.8)', 'rgba(5,150,105,0.8)', 'rgba(217,119,6,0.8)',
 'rgba(220,38,38,0.8)', 'rgba(124,58,237,0.8)', 'rgba(219,39,119,0.8)']
```

**MBTU siempre:** `['#ffc107', '#dc3545']` (Eléctrica amarillo, Térmica rojo)

**Reducción (escala de verdes):** De `rgba(34,197,94,0.8)` a `rgba(20,83,45,0.8)`

**Slate greys (pie nacional):** `['#0f172a', '#1e293b', '#475569', '#64748b', '#94a3b8']`

---

## 14. Hero Sections

### 14.1 Hero Home (Carousel)

```css
min-height: 85vh;
min-height: 600px;
background: #000;

/* Overlay sobre cada slide */
linear-gradient(rgba(15, 23, 42, 0.3), rgba(15, 23, 42, 0.8))

/* Imágenes: position absolute, object-fit cover */
/* Carousel: carousel-fade, interval 4000ms */
/* Badges: bg-primary/success/info bg-opacity-75, border-light, rounded-pill */
```

### 14.2 Hero Centros / Nosotros

```css
background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
/* Lightbulb icon decorativo: 20rem, opacity 0.1, translate(30%, -30%) */
/* Badge: bg-white bg-opacity-10, border border-light, rounded-pill */
/* H1: display-4 fw-bold */
```

### 14.3 Hero Resultados (Más elaborado)

```css
background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #0369a1 70%, #0284c7 100%);
min-height: 100vh;

/* Pseudo-elementos con radial gradients */
/* Floating shapes: 4 círculos con animación float */
/* Grid pattern overlay: cuadrícula 50px con líneas rgba(255,255,255,0.03) */
/* Badge pulsante: dot 8px #22c55e con animation pulse */
/* Título con texto gradiente: -webkit-background-clip: text */
/* Wave separator SVG en la parte inferior */
```

### 14.4 Hero Biblioteca

```css
background: radial-gradient(circle at 10% 20%, #1e293b 0%, #0f172a 90%);
/* Book icon: 15rem, rotate(15deg), opacity 0.1 */
/* Search bar: pill shape, shadow-lg, max-width 500px */
```

---

## 15. Glassmorphism y Efectos Decorativos

### 15.1 Glassmorphism (Resultados)

```css
/* Stat cards principales */
background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.05) 100%);
backdrop-filter: blur(20px);
border: 1px solid rgba(255,255,255,0.15);
border-radius: 24px;

/* Stat cards mini */
background: rgba(255,255,255,0.08);
backdrop-filter: blur(10px);
border: 1px solid rgba(255,255,255,0.1);

/* Filtro card */
background: rgba(255,255,255,0.98);
box-shadow: 0 25px 50px rgba(0,0,0,0.25);

/* Badge hero */
background: rgba(255,255,255,0.1);
border: 1px solid rgba(255,255,255,0.2);
backdrop-filter: blur(10px);
```

### 15.2 Floating Shapes (Resultados)

```css
.floating-shapes .shape {
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.02) 100%);
    animation: float 20s ease-in-out infinite;
}
/* 4 shapes: 400px, 300px, 200px, 150px con delays de -5s */

@keyframes float {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    25%      { transform: translate(10px, -20px) rotate(5deg); }
    50%      { transform: translate(-5px, 10px) rotate(-3deg); }
    75%      { transform: translate(-15px, -10px) rotate(3deg); }
}
```

### 15.3 Grid Pattern Overlay

```css
background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
background-size: 50px 50px;
```

### 15.4 Pulse Dot (Badge Resultados)

```css
.pulse-dot {
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.5; transform: scale(1.2); }
}
```

### 15.5 Wave Separator SVG

```html
<!-- Entre hero y contenido en resultados -->
<div class="wave-separator">
    <svg viewBox="0 0 1440 80" style="width: 100%; height: 80px;">
        <path fill="#f8fafc" d="M0,64L48,58.7C96,...L1440,32L1440,80L0,80Z"/>
    </svg>
</div>
```

### 15.6 Dot Pattern Decorativo (Home/Nosotros)

```html
<svg width="100" height="100">
    <pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">
        <circle cx="2" cy="2" r="2" class="text-primary" fill="currentColor" opacity="0.25"/>
    </pattern>
    <rect width="100" height="100" fill="url(#dots)"/>
</svg>
```

### 15.7 Decoración Circular CTA

```css
/* Dos círculos en esquinas opuestas */
.decoration-circle {
    border-radius: 50%;
    background: rgba(255,255,255,0.1);  /* opacity-10 */
}
/* Top-right: 400x400px, transform: translate(30%, -30%) */
/* Bottom-left: 300x300px, transform: translate(-30%, 30%) */
```

---

## 16. Animaciones

### 16.1 Anime.js - Scroll Animations

```javascript
// Observer trigger
IntersectionObserver con threshold: 0.1

// Animación por defecto (fade-up)
anime({
    targets: element,
    opacity: [0, 1],
    translateY: [40, 0],
    duration: 800,
    easing: 'easeOutQuart',
    delay: element.dataset.delay || 0
});

// Variantes por data-direction:
// "up": translateY [40, 0]
// "down": translateY [-40, 0]
// "left": translateX [40, 0]
// "right": translateX [-40, 0]
```

### 16.2 Anime.js - Counter Animations

```javascript
anime({
    targets: counterObject,
    value: [0, targetValue],
    round: 1,
    duration: 2000,
    delay: 200,
    easing: 'easeOutExpo',
    update: function() {
        element.textContent = prefix + counterObject.value.toLocaleString() + suffix;
    }
});
```

Atributos: `data-count`, `data-prefix`, `data-suffix`

### 16.3 Anime.js - Stagger Grid

```javascript
// Container: .stagger-container, Items: .stagger-item
anime({
    targets: '.stagger-item',
    opacity: [0, 1],
    translateY: [30, 0],
    scale: [0.95, 1],
    delay: anime.stagger(100, { start: 200 }),
    duration: 600,
    easing: 'easeOutQuart'
});
```

### 16.4 Anime.js - Hover Cards

```javascript
// .hover-animate
mouseenter: anime({
    targets: element,
    scale: 1.02,
    translateY: -8,
    boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
    duration: 300,
    easing: 'easeOutQuart'
});

// .hover-icon (dentro de la card)
mouseenter: anime({
    targets: icon,
    scale: 1.2,
    rotate: '10deg',
    duration: 300
});
```

### 16.5 CSS Animations

```css
/* Fade In (resultados) */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Slide Up (resultados) */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up       { animation: slideUp 0.8s ease-out forwards; }
.animate-slide-up-delay { animation: slideUp 0.8s ease-out 0.2s forwards; }

/* Subtle Move (login background) */
@keyframes subtle-move {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    50%      { transform: translate(-2%, -2%) rotate(1deg); }
}

/* Float (resultados shapes) */
@keyframes float { /* ver sección 15.2 */ }

/* Pulse (resultados dot) */
@keyframes pulse { /* ver sección 15.4 */ }

/* Spinner (estado En Ejecución) */
.spinner-grow.spinner-grow-sm {
    width: 0.5rem; height: 0.5rem;
}
```

### 16.6 Transiciones CSS Comunes

| Elemento | Propiedad | Duración | Easing |
|----------|-----------|----------|--------|
| Sidebar | all | 0.3s | ease |
| Nav links | all | 0.2s | - |
| Cards modern | transform, box-shadow | 0.2s | - |
| Hover lift | transform, box-shadow | 0.2s | ease |
| Botones | all | 0.2s-0.3s | ease |
| News cards | transform, box-shadow | 0.3s | cubic-bezier(0.165, 0.84, 0.44, 1) |
| News image | transform | 0.6s | cubic-bezier(0.33, 1, 0.68, 1) |
| Footer links | all | 0.3s | ease |
| Social buttons | all | 0.3s | ease |
| Login inputs | border-color, box-shadow, background | 0.15s | - |
| Stat cards | transform, box-shadow | 0.4s | ease |

### 16.7 Counter Animation Vanilla JS (Resultados)

```javascript
// Sin Anime.js, usa setInterval
const duration = 2000;
const steps = 60;
const stepDuration = duration / steps;
const increment = targetValue / steps;
let current = 0;

const timer = setInterval(() => {
    current += increment;
    if (current >= targetValue) {
        element.textContent = targetValue.toLocaleString('es-CO') + suffix;
        clearInterval(timer);
    } else {
        element.textContent = Math.floor(current).toLocaleString('es-CO') + suffix;
    }
}, stepDuration);
```

---

## 17. Mapa Interactivo

### 17.1 Configuración Leaflet (resultados.html)

```javascript
// Tiles: Carto Positron
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png')

// Centro: Colombia [4.5709, -74.2973]
// Zoom inicial: 6
// Zoom min: 5, max: 18
```

### 17.2 Marcadores

```javascript
// Marcador por centro PEVI
L.circleMarker([lat, lng], {
    radius: 10,          // Puede variar por cantidad de proyectos
    fillColor: color,    // Color del centro (color_primario)
    color: '#fff',       // Borde blanco
    weight: 2,
    opacity: 1,
    fillOpacity: 0.8
})
```

### 17.3 Popup Personalizado

```css
.leaflet-popup-content-wrapper {
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}
.leaflet-popup-content {
    margin: 12px 16px;
}
```

---

## 18. PDF / Informe Impreso

### 18.1 Configuración de Página

```css
@page {
    size: A4;
    margin: 1.5cm 2cm 2cm 1.5cm;
}
@page {
    @bottom-center {
        content: "PEVI Colombia - Informe de Línea Base Energética";
        font-size: 7pt;
        color: #94a3b8;
    }
    @bottom-right {
        content: "Página " counter(page) " de " counter(pages);
        font-size: 7pt;
        color: #94a3b8;
    }
}
```

### 18.2 Portada

```css
/* Fondo: gradiente 135deg #0f172a → #1e3a5f → #0f172a */
/* Overlay pattern: radial gradients cyan y green */
/* Dimensiones: 210mm x 297mm (A4) */

/* Estructura vertical: */
/* Top: Logo (90px, inverted) + Badge "Informe Oficial" */
/* Center: Subtítulo (#38bdf8, 11pt, uppercase, 3px spacing) */
/*         Título (white, 32pt, fw-700) */
/*         Empresa (#94a3b8, 16pt, fw-300) */
/*         Grid metadata (4 items: Centro, Sector, Fecha, Fase) */
/* Bottom: Logos aliados (25px, opacity 0.5) */
```

### 18.3 KPI Cards PDF

```css
/* Layout: display table con 4 celdas */
background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
border: 1px solid #e2e8f0;
border-radius: 10px;
padding: 12px 8px;
text-align: center;

/* Variante destacada */
background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
color: white;

/* Cambio positivo/negativo */
/* Positivo: bg #dcfce7, color #22c55e */
/* Negativo: bg #fee2e2, color #ef4444 */
```

### 18.4 Tablas PDF

```css
/* Header: bg #0f172a, white text, 8pt uppercase */
/* Body: 9pt, border-bottom 1px solid #e2e8f0 */
/* Alternancia: nth-child(even) bg #f8fafc */
/* Total: bg #f1f5f9, fw-700, border-top 2px solid #0f172a */
```

### 18.5 Gráficos CSS (Barras) para PDF

```css
/* Track: height 20px, background #f1f5f9, border-radius 4px */
/* Fill: ancho dinámico (%), border-radius 4px, color blanco texto */
/* Colores por fuente energética (mismos que Chart.js) */
```

### 18.6 Highlight Boxes PDF

```css
/* Success */
background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
border: 1px solid #86efac;
title-color: #166534;

/* Warning */
background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
border: 1px solid #fbbf24;
title-color: #92400e;
```

### 18.7 Secciones con Barra de Color

```css
/* Cada sección tiene una barra lateral decorativa */
.section-title::before {
    width: 4px;
    height: 20px;
    background: linear-gradient(to bottom, #0ea5e9, #22c55e);
    border-radius: 2px;
}
```

---

## 19. Página de Login

### 19.1 Layout Two-Column Grid

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────────┬──────────────────────────┐    │
│  │   FORM PANEL     │    BRAND PANEL           │    │
│  │   (bg: #fdfdfd)  │    (imagen + overlay)    │    │
│  │                  │                          │    │
│  │   [Logo PEVI]    │    [Logos Centros]        │    │
│  │   Iniciar Sesión │    "Plataforma Nacional   │    │
│  │   "Accede al..." │     de Gestión..."       │    │
│  │                  │                          │    │
│  │   [Usuario]      │    Overlay:              │    │
│  │   [Contraseña]   │    radial-gradient       │    │
│  │                  │    + saturate + blur      │    │
│  │   [INGRESAR]     │                          │    │
│  │                  │                          │    │
│  │   ¿Olvidaste?    │                          │    │
│  │   ─────────────  │                          │    │
│  │   Aliados [logos] │                          │    │
│  └──────────────────┴──────────────────────────┘    │
│                                                     │
│  Background: gradiente oscuro + grid pattern        │
│  + radial gradients animados (subtle-move 20s)      │
└─────────────────────────────────────────────────────┘
```

**Shell (contenedor):**
- Max-width: 1100px, min-height: 560px
- Border-radius: 28px
- Grid: 1fr 0.9fr
- Sombra: triple layer

**Form Panel:**
- Padding: 2.8rem 3rem
- Input: border-radius 0.75rem, bg `#f9fafb`, focus border `#111827`
- Botón: pill negro `#111827`, uppercase, shadow fuerte
- Error: bg `#fef2f2`, border `#fee2e2`, dot rojo `#ef4444`
- Aliados: grayscale(80%) → grayscale(0%) hover

**Brand Panel:**
- Imagen de fondo `energy.png` con overlay oscuro + blur
- Logos centros: 64px, `brightness(0) invert(1)`, hover translateY(-1px)

---

## 20. Sitio Público vs App Interna

| Aspecto | App Interna | Sitio Público |
|---------|-------------|---------------|
| **Font** | Inter | Work Sans |
| **Layout** | Sidebar fijo 260px | Navbar top fijo |
| **Fondo** | `#f1f5f9` (slate-100) | `#f5f5f5` |
| **Cards** | `.card-modern` (12px radius, shadow-sm) | Cards custom con hover elevación |
| **Colores** | Palette Tailwind/Slate | Palette UPME (green, blue) |
| **Navegación** | Sidebar colapsable | Navbar horizontal con dropdown |
| **Animaciones** | Mínimas (hover lift, transitions) | Anime.js completo (scroll, counters, stagger) |
| **Gráficos** | Chart.js inline | Chart.js + Leaflet mapa |
| **Hero** | No tiene | Hero sections con gradientes |
| **Footer** | No tiene | Footer completo 4 columnas |
| **Gov.co** | No | Barra gubernamental top |

---

## 21. Responsive

### 21.1 Breakpoints Utilizados

| Breakpoint | Uso |
|------------|-----|
| `max-width: 991px` | Sidebar collapse, navbar mobile, body padding-top 70px |
| `max-width: 992px` | Stat cards reducidos (resultados), padding-top 2rem |
| `max-width: 900px` | Login: grid 1fr, brand panel order -1, max-width 560px |
| `max-width: 768px` | Footer stack, filter grid 2 cols, stat mobile sizes |
| `max-width: 600px` | Login padding reducido, logos 52px, filter grid 1 col |
| `max-width: 480px` | Filter grid 1 col (resultados) |

### 21.2 Sidebar Mobile

- Se oculta en pantallas < 991px
- Contenido usa full width (margin-left: 0)
- Body recibe padding-top: 70px para compensar

### 21.3 Navbar Público Mobile

```css
@media (max-width: 991px) {
    .nav-upme { flex-direction: column; padding: 15px 0; }
    .nav-upme .nav-link { width: 100%; padding: 12px 16px; }
    .govco-right-links span { display: none; }
    .btn-portal { font-size: 0.75rem; padding: 0.4rem 1.1rem; }
}
```

---

## 22. Iconografía

### 22.1 Librería

**Bootstrap Icons 1.11.0** (CDN: `cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0`)

### 22.2 Íconos por Contexto

| Contexto | Ícono | Clase |
|----------|-------|-------|
| Dashboard | `bi-speedometer2` | Sidebar |
| Proyectos | `bi-folder2-open` | Sidebar, KPIs |
| Empresas | `bi-building` | Sidebar, tabla |
| Equipo | `bi-people` | Sidebar |
| Métricas | `bi-graph-up-arrow` | Sidebar |
| Control Panel | `bi-gear-wide-connected` | Sidebar |
| Electricidad | `bi-plug-fill` | Cards energía |
| Gas Natural | `bi-fire` | Cards energía |
| Carbón | `bi-box-seam-fill` | Cards energía |
| Fuel Oil | `bi-droplet-fill` | Cards energía |
| Biomasa | `bi-recycle` | Cards energía |
| Gas Propano | `bi-cloud-fog2-fill` | Cards energía |
| Energía total | `bi-lightning-charge-fill` | KPIs |
| Emisiones | `bi-globe-americas` | KPIs |
| Costos | `bi-currency-dollar` | KPIs |
| Calendario | `bi-calendar3` | Fechas |
| Editar | `bi-pencil` | Botones acción |
| Eliminar | `bi-trash` | Botones acción |
| Descargar | `bi-download` | Documentos |
| Subir | `bi-cloud-upload` | Modal upload |
| Buscar | `bi-search` | Inputs búsqueda |
| Filtrar | `bi-funnel` | Secciones filtro |
| Ubicación | `bi-geo-alt` / `bi-geo-alt-fill` | Mapa, contacto |
| Usuario | `bi-person-circle` | Perfiles |
| Estrella | `bi-star-fill` | Líder actual |
| Check | `bi-check-circle-fill` | Estado finalizado |
| Warning | `bi-exclamation-triangle-fill` | Alertas |
| Info | `bi-info-circle-fill` | Información |
| PDF | `bi-file-earmark-pdf` | Documentos |
| Reducción | `bi-graph-down-arrow` | Modal reducción |
| Trofeo | `bi-trophy-fill` | Ranking nacional |
| Bandera | `bi-flag-fill` | Fases |
| Reloj | `bi-clock-history` | Actividad reciente |
| Home | `bi-house-door` | Breadcrumbs |
| Cerrar sesión | `bi-box-arrow-right` | Sidebar |

---

## Apéndice: Archivos de Imagen Estáticos

Ubicación: `/static/img/`

| Archivo | Uso |
|---------|-----|
| `logo_pevi.png` | Logo principal (sidebar, navbar, login, PDF) |
| `logo_2.png` | Logo alternativo |
| `logo_minenergia.png` | Ministerio de Energía (footer, aliados) |
| `logo_upme.png` | UPME (footer, aliados) |
| `logo_onudi.png` | ONUDI (footer, aliados) |
| `Logo_de_la_Universidad_del_Atlántico.svg.png` | Centro PEVI (login) |
| `Logo_UAO.svg.png` | Centro PEVI (login) |
| `logo_uvigo.png` | Centro PEVI (login) |
| `logo_utp.png` | Centro PEVI (login) |
| `logo_ufps.png` | Centro PEVI (login) |
| `energy.png` | Fondo panel brand login |
| `cover_bombeo.png` | Biblioteca |
| `cover_motores.png` | Biblioteca |
| `cover_vapor.png` | Biblioteca |
