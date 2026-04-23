#!/usr/bin/env python3
"""
cargar_excel_pevi.py

Carga del consolidado Excel (Hoja1) a la BD de producción de PEVI.
Diseñado para correr EN PRODUCCIÓN, idempotente, transaccional.

============================================================
USO
============================================================

# Modo seguro (DRY-RUN — default): no toca BD, solo muestra lo que haría
python cargar_excel_pevi.py

# Aplicar TODO (cleanup + profesores + carga)
python cargar_excel_pevi.py --apply

# Solo una fase
python cargar_excel_pevi.py --apply --solo cleanup
python cargar_excel_pevi.py --apply --solo profesores
python cargar_excel_pevi.py --apply --solo carga

# Cuando hay matches dudosos: editar matches_dudosos.json y volver a correr
python cargar_excel_pevi.py --apply --matches matches_dudosos.json

============================================================
ARCHIVOS GENERADOS
============================================================

plan_carga.txt        — reporte legible (modo dry-run)
matches_dudosos.json  — empresas ambiguas a confirmar manualmente
log_aplicacion.txt    — log detallado tras --apply

============================================================
REQUISITOS
============================================================

pip install openpyxl
"""

import os
import re
import sys
import json
import argparse
import traceback
import unicodedata
from datetime import date
from collections import defaultdict
from difflib import SequenceMatcher

# === Setup Django ===
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from gestion.models import CentroPevi, Usuario
from auditorias.models import (
    Empresa, ProyectoAuditoria,
    Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano,
)

import openpyxl


# ============================================================
# CONSTANTES Y MAPEOS
# ============================================================

EXCEL_FILE = 'Consolidado Enero 2026 (4).xlsx'

# Excel "Centro Pevi" → DB nombre_corto
MAPEO_CENTROS_EXCEL = {
    'UNAB': 'UNAB',
    'UAO': 'UAO',
    'UNIATLANTICO': 'UA',
}

# Profesores en Excel ya existentes en BD (decisiones del usuario)
PROFESORES_MATCH_EXISTENTE = {
    'Carlos Diaz': 2, 'Carlos Díaz': 2,
    'Luis Jaimes': 3,
    'Mario Acero': 4,
    'Leonardo Pacheco': 5,
    'Yecid Muñoz': 6,
    'César Acevedo': 7,
    'Juan Carlos Campos': 8,
    'Jorge Eliecer Duarte': 11,        # = Jorge Duarte Forero (id=11) por decisión
    'Jorge Eliecer Duarte ': 11,       # variante con espacio
    'Jorge Duarte Forero': 11,
}

# Profesores a CREAR (no existen en BD).  (excel_name, centro_corto, first_name, last_name)
PROFESORES_A_CREAR = [
    ('Félix González Pérez',     'UAO', 'Félix',     'González Pérez'),
    ('Guillermo Valencia Ochoa', 'UA',  'Guillermo', 'Valencia Ochoa'),
    ('Jairo Palacios',           'UA',  'Jairo',     'Palacios'),
    ('Lourdes Meriño Stand',     'UA',  'Lourdes',   'Meriño Stand'),
    ('Marley Vanegas',           'UA',  'Marley',    'Vanegas'),
    ('Paola Barros',             'UA',  'Paola',     'Barros'),
    ('Rosaura Castrillón',       'UA',  'Rosaura',   'Castrillón'),
]

PLACEHOLDER_DOMAIN = 'placeholder.pevicolombia.com'

# CLEANUP
EMPRESAS_TEST_NOMBRES = ['Centro comercial X', 'INDUNILO SAS', 'Empresa Prueba']
DUPLICADOS_BORRAR = [36, 47, 55]   # FANALCA-2, CELCO-2, Baxter-2 (decisión usuario)

# Mover empresas de centro UA → UAO (decisión usuario)
EMPRESAS_MOVER_CENTRO = {
    21: 'UAO',  # Eka Zipper
    22: 'UAO',  # Alumina
    23: 'UAO',  # Provider SAS
}

# Mapeo de fases
FASE_EXCEL_TO_DB = {1: 'FASE_1', 2: 'FASE_2', 3: 'FASE_3', 4: 'FASE_4'}

# Índices de columnas Excel (0-based)
META_COLS = {
    'fase': 0, 'año': 1, 'centro': 2, 'empresa': 3, 'sector': 4,
    'lider': 5, 'comentarios': 6, 'produccion': 7, 'unidad_produccion': 8,
}

# Mapeo de columnas por fuente. Tuplas (campo_django, idx_0based)
COLS_ELECTRICIDAD = [
    ('consumo_mensual',          9),   # col 10
    ('consumo_anual',           10),
    ('costo_unitario',          12),
    ('costo_mensual_promedio',  13),
    ('costo_total_anual',       14),
    ('factor_emision',          15),
    ('emisiones_totales',       16),
]

COLS_GAS_NATURAL = [
    ('consumo_mensual_orig',    17),
    ('consumo_anual_orig',      18),
    ('costo_unitario',          19),
    ('costo_mensual_promedio',  20),
    ('costo_total_anual',       21),
    ('poder_calorifico',        22),
    ('factor_emision',          26),
    ('emisiones_totales',       27),
]

COLS_CARBON = [
    ('consumo_mensual_orig',    28),
    ('consumo_anual_orig',      29),
    ('costo_unitario',          30),
    ('costo_mensual_promedio',  31),
    ('costo_total_anual',       32),
    ('poder_calorifico',        33),
    ('factor_emision',          37),
    ('emisiones_totales',       38),
]

COLS_FUELOIL = [
    ('consumo_mensual_orig',    39),
    ('consumo_anual_orig',      40),
    ('costo_unitario',          41),
    ('costo_mensual_promedio',  42),
    ('costo_total_anual',       43),
    ('poder_calorifico',        44),
    ('factor_emision',          48),
    ('emisiones_totales',       49),
]

COLS_BIOMASA = [
    ('consumo_mensual_orig',    50),
    ('consumo_anual_orig',      51),
    ('costo_unitario',          52),
    ('costo_mensual_promedio',  53),
    ('costo_total_anual',       54),
    ('poder_calorifico',        55),
    ('factor_emision',          59),
    ('emisiones_totales',       60),
]

COLS_GLP = [
    ('consumo_mensual_orig',    61),
    ('consumo_anual_orig',      62),
    ('costo_unitario',          63),
    ('costo_mensual_promedio',  64),
    ('costo_total_anual',       65),
    ('poder_calorifico',        66),
    ('factor_emision',          70),
    ('emisiones_totales',       71),
]

# Cols % reducción (0-based) — Excel los guarda como fracción (0.0598 = 5.98%)
COL_PCT = {
    'electricidad': 77,
    'gas_natural':  78,
    'carbon':       79,
    'fuel_oil':     80,
    'biomasa':      81,
    'glp':          82,
}

# (nombre_clave, ModelClass, cols_def, idx_consumo_check, multiplica_pct)
FUENTES_DEF = [
    ('electricidad', Electricidad,  COLS_ELECTRICIDAD, 10),  # check consumo_anual
    ('gas_natural',  GasNatural,    COLS_GAS_NATURAL,  18),  # check consumo_anual_orig
    ('carbon',       CarbonMineral, COLS_CARBON,       29),
    ('fuel_oil',     FuelOil,       COLS_FUELOIL,      40),
    ('biomasa',      Biomasa,       COLS_BIOMASA,      51),
    ('glp',          GasPropano,    COLS_GLP,          62),
]


# ============================================================
# HELPERS
# ============================================================

def to_float(v):
    if v in (None, '', '-'):
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def normalizar(s):
    if not s:
        return ''
    s = str(s).strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.,\-_/()&]+', ' ', s)
    s = re.sub(r'\b(s\.?a\.?(s\.?)?|ltda|sas|cia)\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def similitud(a, b):
    return SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()


def estado_desde_comentario(coment):
    if coment and 'completo' in str(coment).lower():
        return 'FINALIZADO'
    return 'EJECUCION'


def cargar_excel():
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb['Hoja1']
    rows = list(ws.iter_rows(values_only=True))
    return [r for r in rows[2:] if r[META_COLS['centro']] is not None
            and str(r[META_COLS['centro']]).strip()]


# ============================================================
# REPORTER
# ============================================================

class Reporter:
    LEVELS = {'info': '   ', 'ok': ' + ', 'warn': ' ! ', 'err': ' X '}

    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.lines = []
        self.summary = defaultdict(int)

    def log(self, msg, level='info'):
        prefix = self.LEVELS.get(level, '   ')
        line = f'{prefix}{msg}'
        print(line)
        self.lines.append(line)

    def section(self, title):
        line = '\n' + '=' * 72 + '\n' + title + '\n' + '=' * 72
        print(line)
        self.lines.append(line)

    def count(self, key, n=1):
        self.summary[key] += n

    def save(self, path):
        with open(path, 'w') as f:
            f.write('\n'.join(self.lines))
            f.write('\n\n=== RESUMEN ===\n')
            for k, v in sorted(self.summary.items()):
                f.write(f'  {k}: {v}\n')


# ============================================================
# FASE 1 — CLEANUP
# ============================================================

def fase_cleanup(rep, dry_run):
    rep.section('FASE 1 — CLEANUP')

    centros_db = {c.nombre_corto: c for c in CentroPevi.objects.all()}

    # 1a. Borrar empresas duplicadas
    rep.log('--- Empresas duplicadas a borrar ---')
    for emp_id in DUPLICADOS_BORRAR:
        try:
            e = Empresa.objects.get(id=emp_id)
        except Empresa.DoesNotExist:
            rep.log(f'Empresa id={emp_id} no existe (¿ya borrada?)', 'warn')
            continue

        proyectos = list(e.auditorias.all())
        if proyectos:
            rep.log(f'Empresa id={emp_id} ({e.razon_social}) tiene {len(proyectos)} proyectos — se borrarán', 'warn')
            for p in proyectos:
                rep.log(f'  - BORRAR proyecto id={p.id}: {p.nombre_proyecto}', 'ok')
                if not dry_run:
                    p.delete()
                rep.count('proyectos_borrados')

        rep.log(f'BORRAR empresa duplicada id={emp_id}: {e.razon_social} (NIT {e.nit})', 'ok')
        if not dry_run:
            e.delete()
        rep.count('empresas_duplicadas_borradas')

    # 1b. Borrar empresas de prueba
    rep.log('')
    rep.log('--- Empresas de prueba a borrar ---')
    for nombre in EMPRESAS_TEST_NOMBRES:
        empresas = Empresa.objects.filter(razon_social=nombre)
        if not empresas.exists():
            rep.log(f'Empresa "{nombre}" no existe (¿ya borrada?)', 'warn')
            continue
        for e in empresas:
            for p in e.auditorias.all():
                rep.log(f'  - BORRAR proyecto id={p.id}: {p.nombre_proyecto}', 'ok')
                if not dry_run:
                    p.delete()
                rep.count('proyectos_borrados')
            rep.log(f'BORRAR empresa de prueba: {nombre} (id={e.id})', 'ok')
            if not dry_run:
                e.delete()
            rep.count('empresas_test_borradas')

    # 1c. Mover empresas de centro (atómico con sus proyectos)
    rep.log('')
    rep.log('--- Empresas a mover de centro ---')
    for emp_id, nuevo_corto in EMPRESAS_MOVER_CENTRO.items():
        try:
            e = Empresa.objects.get(id=emp_id)
        except Empresa.DoesNotExist:
            rep.log(f'Empresa id={emp_id} no existe', 'err')
            continue

        nuevo_centro = centros_db.get(nuevo_corto)
        if not nuevo_centro:
            rep.log(f'Centro "{nuevo_corto}" no existe en BD', 'err')
            continue

        centro_actual = e.centro.nombre_corto if e.centro else 'NULL'
        if centro_actual == nuevo_corto:
            rep.log(f'Empresa id={emp_id} ya está en {nuevo_corto}, skip', 'info')
            continue

        rep.log(f'MOVER empresa "{e.razon_social}" (id={emp_id}): {centro_actual} → {nuevo_corto}', 'ok')
        proyectos = list(e.auditorias.all())
        for p in proyectos:
            rep.log(f'  - también moviendo proyecto id={p.id}: {p.nombre_proyecto}', 'info')

        if not dry_run:
            # Atomic: empresa + proyectos via .update() (raw SQL) para brincar
            # la validación de save() del modelo ProyectoAuditoria que exige
            # consistencia centro_proyecto == centro_empresa en todo momento.
            # Como ambas filas se actualizan en la misma transacción, queda
            # consistente al final.
            with transaction.atomic():
                ProyectoAuditoria.objects.filter(empresa_id=e.id).update(centro_id=nuevo_centro.id)
                Empresa.objects.filter(id=e.id).update(centro_id=nuevo_centro.id)
        rep.count('empresas_movidas')


# ============================================================
# FASE 2 — CREAR PROFESORES FALTANTES
# ============================================================

def fase_crear_profesores(rep, dry_run):
    rep.section('FASE 2 — Crear profesores faltantes')
    centros_db = {c.nombre_corto: c for c in CentroPevi.objects.all()}

    for excel_name, centro_corto, fname, lname in PROFESORES_A_CREAR:
        # Generar username único
        base_user = (fname + lname).lower()
        base_user = unicodedata.normalize('NFD', base_user)
        base_user = ''.join(c for c in base_user if unicodedata.category(c) != 'Mn')
        base_user = re.sub(r'[^a-z0-9]', '', base_user)[:25]
        username = base_user
        idx = 0
        while Usuario.objects.filter(username=username).exists():
            idx += 1
            username = f'{base_user}{idx}'
        email = f'{username}@{PLACEHOLDER_DOMAIN}'

        if Usuario.objects.filter(email=email).exists():
            rep.log(f'Email {email} ya existe — saltando {excel_name}', 'warn')
            continue

        # Verificar si ya existe alguien con esos nombres exactos (evitar dups si se reejecuta)
        ya_existe = Usuario.objects.filter(first_name=fname, last_name=lname).first()
        if ya_existe:
            rep.log(f'Profesor "{fname} {lname}" ya existe (id={ya_existe.id}), skip', 'info')
            continue

        rep.log(f'CREAR profesor: {fname} {lname} (PROFESOR/{centro_corto}) — username={username}', 'ok')
        if not dry_run:
            u = Usuario(
                username=username,
                email=email,
                first_name=fname,
                last_name=lname,
                rol='PROFESOR',
                centro_pevi=centros_db[centro_corto],
                is_active=True,
            )
            u.set_unusable_password()  # Login requiere password reset
            u.save()
        rep.count('profesores_creados')


# ============================================================
# FASE 3 — PLAN DE EMPRESAS (matches dudosos)
# ============================================================

def planificar_empresas(rep, matches_file=None):
    rep.section('FASE 3 — Mapeo de empresas Excel ↔ BD')

    excel_rows = cargar_excel()

    # Empresas existentes agrupadas por centro_corto
    emp_por_centro = defaultdict(list)
    for e in Empresa.objects.select_related('centro'):
        if e.centro_id:
            emp_por_centro[e.centro.nombre_corto].append(e)

    # Cargar confirmaciones manuales si existen
    confirmaciones = {}
    if matches_file and os.path.exists(matches_file):
        with open(matches_file) as f:
            data = json.load(f)
            confirmaciones = {item['key']: item.get('decision')
                              for item in data.get('matches_dudosos', [])}
        rep.log(f'Cargadas {len(confirmaciones)} confirmaciones de "{matches_file}"', 'info')

    plan = []
    dudosos = []

    for r in excel_rows:
        excel_centro = r[META_COLS['centro']]
        excel_empresa = r[META_COLS['empresa']]

        centro_corto = MAPEO_CENTROS_EXCEL.get(excel_centro)
        if not centro_corto:
            rep.log(f'Centro "{excel_centro}" no mapeado para "{excel_empresa}" — fila omitida', 'err')
            continue

        candidatos = emp_por_centro.get(centro_corto, [])
        mejor_score = 0.0
        mejor_emp = None
        for e in candidatos:
            s = similitud(excel_empresa, e.razon_social)
            if s > mejor_score:
                mejor_score = s
                mejor_emp = e

        key = f'{centro_corto}::{normalizar(excel_empresa)}'

        # Match seguro (≥0.95 o normalizado idéntico)
        if mejor_emp and (mejor_score >= 0.95 or
                          normalizar(excel_empresa) == normalizar(mejor_emp.razon_social)):
            plan.append({'excel_row': r, 'accion': 'reusar_empresa',
                         'empresa_id': mejor_emp.id, 'similitud': round(mejor_score, 3)})
        elif mejor_emp and mejor_score >= 0.70:
            # Dudoso
            decision = confirmaciones.get(key, '__NO_DEFINIDO__')
            if decision == '__NO_DEFINIDO__':
                # Agregar a dudosos para confirmación manual
                dudosos.append({
                    'key': key,
                    'excel_nombre': excel_empresa,
                    'excel_centro': excel_centro,
                    'similitud': round(mejor_score, 3),
                    'candidato_db_id': mejor_emp.id,
                    'candidato_db_nombre': mejor_emp.razon_social,
                    'candidato_db_nit': mejor_emp.nit,
                    'decision': mejor_emp.id,
                    '_instrucciones': "Cambia 'decision' a null para crear nueva empresa, deja el ID para confirmar match",
                })
                plan.append({'excel_row': r, 'accion': 'pendiente'})
            elif decision is None:
                plan.append({'excel_row': r, 'accion': 'crear_empresa', 'empresa_id': None})
            else:
                plan.append({'excel_row': r, 'accion': 'reusar_empresa',
                             'empresa_id': decision, 'confirmado_manual': True})
        else:
            # Match malo o no hay candidatos → crear nueva
            plan.append({'excel_row': r, 'accion': 'crear_empresa', 'empresa_id': None})

    n_reusar = sum(1 for p in plan if p['accion'] == 'reusar_empresa')
    n_crear = sum(1 for p in plan if p['accion'] == 'crear_empresa')
    n_pendiente = sum(1 for p in plan if p['accion'] == 'pendiente')
    rep.log(f'Empresas a reusar:    {n_reusar}', 'ok')
    rep.log(f'Empresas a crear:     {n_crear}', 'ok')
    rep.log(f'Pendientes (dudosos): {n_pendiente}',
            'warn' if n_pendiente else 'info')

    return plan, dudosos


# ============================================================
# FASE 4 — CARGA EFECTIVA
# ============================================================

def construir_mapa_profesores():
    """Devuelve dict normalize(excel_name) → Usuario."""
    out = {}
    for excel_name, db_id in PROFESORES_MATCH_EXISTENTE.items():
        u = Usuario.objects.filter(id=db_id).first()
        if u:
            out[normalizar(excel_name)] = u
    for excel_name, _, fname, lname in PROFESORES_A_CREAR:
        u = Usuario.objects.filter(first_name=fname, last_name=lname).first()
        if u:
            out[normalizar(excel_name)] = u
    return out


def aplicar_carga(rep, plan, dry_run):
    rep.section('FASE 4 — Carga de proyectos y fuentes energéticas')

    centros_db = {c.nombre_corto: c for c in CentroPevi.objects.all()}
    profesor_map = construir_mapa_profesores()

    for item in plan:
        if item['accion'] == 'pendiente':
            continue

        r = item['excel_row']
        excel_centro_str = r[META_COLS['centro']]
        excel_empresa_nombre = r[META_COLS['empresa']]
        excel_sector = r[META_COLS['sector']] or 'Sin clasificar'
        excel_lider = r[META_COLS['lider']]
        excel_año = r[META_COLS['año']]
        excel_fase = r[META_COLS['fase']]
        excel_coment = r[META_COLS['comentarios']]
        excel_prod = to_float(r[META_COLS['produccion']])
        excel_unidad = r[META_COLS['unidad_produccion']] or 'unidades'

        centro = centros_db[MAPEO_CENTROS_EXCEL[excel_centro_str]]

        # ========== EMPRESA ==========
        empresa = None
        if item['accion'] == 'reusar_empresa':
            empresa = Empresa.objects.filter(id=item['empresa_id']).first()
            if empresa:
                rep.log(f'[{excel_empresa_nombre}] usar empresa existente id={empresa.id}', 'ok')
        else:
            # Crear empresa con NIT temporal único
            nit_temp = f'TMP-{normalizar(excel_empresa_nombre).replace(" ", "")[:20]}'
            base_nit = nit_temp
            i = 0
            while Empresa.objects.filter(nit=nit_temp).exists():
                i += 1
                nit_temp = f'{base_nit}-{i}'
            rep.log(f'[{excel_empresa_nombre}] CREAR empresa nueva en {centro.nombre_corto} (NIT temporal: {nit_temp})', 'ok')
            if not dry_run:
                empresa = Empresa.objects.create(
                    centro=centro,
                    razon_social=excel_empresa_nombre[:200],
                    nit=nit_temp[:20],
                    sector_productivo=str(excel_sector)[:100],
                    direccion=(centro.ciudad or 'Sin dirección')[:255],
                    ciudad=(centro.ciudad or 'Sin ciudad')[:100],
                    contacto_nombre='Sin contacto',
                    contacto_email=f'sincontacto@{PLACEHOLDER_DOMAIN}',
                    contacto_telefono='N/A',
                )
                rep.count('empresas_creadas')

        if empresa is None and not dry_run:
            rep.log(f'   No se pudo resolver empresa, fila omitida', 'err')
            continue

        # ========== LIDER ==========
        lider = None
        if excel_lider and str(excel_lider).strip() not in ('-', ''):
            lider = profesor_map.get(normalizar(str(excel_lider)))
            if not lider:
                rep.log(f'   Líder "{excel_lider}" no encontrado — proyecto sin líder', 'warn')

        # ========== PROYECTO (reutilizar por (empresa, año)) ==========
        proy = None
        if empresa is not None:
            proy = ProyectoAuditoria.objects.filter(
                empresa=empresa, fecha_inicio__year=int(excel_año)
            ).first()
        elif item['accion'] == 'reusar_empresa':
            proy = ProyectoAuditoria.objects.filter(
                empresa_id=item['empresa_id'], fecha_inicio__year=int(excel_año)
            ).first()

        if proy:
            rep.log(f'   Reusar proyecto existente id={proy.id}: "{proy.nombre_proyecto[:60]}"', 'ok')
            rep.count('proyectos_reusados')
        else:
            nombre_proy = f'Auditoría Energética {excel_año} - {excel_empresa_nombre}'[:200]
            estado = estado_desde_comentario(excel_coment)
            try:
                fase_db = FASE_EXCEL_TO_DB.get(int(excel_fase)) if excel_fase else None
            except (ValueError, TypeError):
                fase_db = None
            rep.log(f'   CREAR proyecto "{nombre_proy[:60]}" (fase={fase_db}, estado={estado})', 'ok')
            if not dry_run and empresa:
                proy = ProyectoAuditoria.objects.create(
                    centro=centro,
                    empresa=empresa,
                    lider_proyecto=lider,
                    nombre_proyecto=nombre_proy,
                    fecha_inicio=date(int(excel_año), 1, 1),
                    estado=estado,
                    fase=fase_db,
                    produccion_total=excel_prod,
                    unidad_produccion=str(excel_unidad)[:50],
                )
                rep.count('proyectos_creados')

        # ========== FUENTES ENERGÉTICAS ==========
        if proy and not dry_run:
            cargar_fuentes(rep, proy, r)
        elif dry_run:
            # En dry-run solo reportamos qué fuentes se cargarían
            for nombre, _, _, idx_check in FUENTES_DEF:
                if to_float(r[idx_check]) > 0:
                    rep.log(f'      → cargaría fuente {nombre}', 'info')


def cargar_fuentes(rep, proy, r):
    """Carga las 6 fuentes para un proyecto si vienen con consumo > 0. Idempotente."""
    for nombre_fuente, model_cls, cols, idx_check in FUENTES_DEF:
        consumo = to_float(r[idx_check])
        if consumo <= 0:
            continue

        # Idempotencia: si ya existe, skip
        related = f'{model_cls._meta.model_name}_related'
        if getattr(proy, related).exists():
            rep.log(f'      {nombre_fuente}: ya existe en proyecto, skip', 'info')
            continue

        # Construir kwargs desde cols
        kwargs = {'proyecto': proy}
        for campo, idx in cols:
            kwargs[campo] = to_float(r[idx])

        # % reducción (Excel: fracción → BD: porcentaje)
        pct_idx = COL_PCT.get(nombre_fuente)
        if pct_idx is not None:
            kwargs['porcentaje_reduccion'] = to_float(r[pct_idx]) * 100

        try:
            model_cls.objects.create(**kwargs)
            rep.log(f'      + {nombre_fuente} cargada (consumo={consumo})', 'ok')
            rep.count(f'fuentes_{nombre_fuente}')
        except Exception as ex:
            rep.log(f'      X ERROR cargando {nombre_fuente}: {ex}', 'err')
            rep.count('fuentes_errores')


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Carga del Excel consolidado a BD PEVI')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (default: dry-run)')
    parser.add_argument('--matches', help='Archivo JSON con confirmaciones de matches dudosos')
    parser.add_argument('--solo', choices=['cleanup', 'profesores', 'carga'],
                        help='Ejecutar solo una fase')
    args = parser.parse_args()

    dry_run = not args.apply
    rep = Reporter(dry_run=dry_run)
    rep.section(f'CARGADOR EXCEL → BD PEVI ({"DRY-RUN" if dry_run else "APPLY"})')
    rep.log(f'Excel: {EXCEL_FILE}')
    rep.log(f'Modo: {"DRY-RUN (no toca BD)" if dry_run else "APPLY (modifica BD)"}')

    if not os.path.exists(EXCEL_FILE):
        rep.log(f'No encuentro el Excel: {EXCEL_FILE}', 'err')
        return 1

    # === FASE 1: CLEANUP ===
    if not args.solo or args.solo == 'cleanup':
        try:
            if dry_run:
                fase_cleanup(rep, dry_run=True)
            else:
                with transaction.atomic():
                    fase_cleanup(rep, dry_run=False)
        except Exception as e:
            rep.log(f'Error en cleanup: {e}', 'err')
            rep.log(traceback.format_exc(), 'err')
            rep.save('log_aplicacion.txt')
            return 1

    # === FASE 2: PROFESORES ===
    if not args.solo or args.solo == 'profesores':
        try:
            if dry_run:
                fase_crear_profesores(rep, dry_run=True)
            else:
                with transaction.atomic():
                    fase_crear_profesores(rep, dry_run=False)
        except Exception as e:
            rep.log(f'Error creando profesores: {e}', 'err')
            rep.log(traceback.format_exc(), 'err')
            rep.save('log_aplicacion.txt')
            return 1

    # === FASE 3+4: PLANIFICAR Y CARGAR ===
    if not args.solo or args.solo == 'carga':
        try:
            plan, dudosos = planificar_empresas(rep, args.matches)
        except Exception as e:
            rep.log(f'Error planificando: {e}', 'err')
            rep.log(traceback.format_exc(), 'err')
            rep.save('log_aplicacion.txt')
            return 1

        if dudosos:
            archivo_dudosos = 'matches_dudosos.json'
            with open(archivo_dudosos, 'w', encoding='utf-8') as f:
                json.dump({'matches_dudosos': dudosos}, f, indent=2, ensure_ascii=False)
            rep.log('')
            rep.log(f'⚠ Generado "{archivo_dudosos}" con {len(dudosos)} matches a confirmar.', 'warn')
            rep.log(f'   Edita el archivo: cambia "decision" a null para crear nueva, o deja el ID para reusar.', 'warn')
            rep.log(f'   Luego corre: python {sys.argv[0]} --apply --matches {archivo_dudosos}', 'warn')
            if args.apply:
                rep.log('   No aplico la carga hasta resolver matches dudosos.', 'warn')
                rep.save('plan_carga.txt')
                return 0

        try:
            if dry_run:
                aplicar_carga(rep, plan, dry_run=True)
            else:
                with transaction.atomic():
                    aplicar_carga(rep, plan, dry_run=False)
        except Exception as e:
            rep.log(f'Error en carga: {e}', 'err')
            rep.log(traceback.format_exc(), 'err')
            rep.save('log_aplicacion.txt')
            return 1

    # === RESUMEN ===
    rep.section('RESUMEN FINAL')
    if not rep.summary:
        rep.log('Sin cambios registrados', 'info')
    else:
        for k, v in sorted(rep.summary.items()):
            rep.log(f'{k}: {v}', 'ok')

    rep.save('plan_carga.txt' if dry_run else 'log_aplicacion.txt')
    print(f'\n{"DRY-RUN" if dry_run else "APLICACIÓN"} completado.')
    print(f'Reporte guardado en: {"plan_carga.txt" if dry_run else "log_aplicacion.txt"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
