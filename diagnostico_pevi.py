#!/usr/bin/env python3
"""
Script de diagnóstico READ-ONLY del sistema PEVI.

Genera un JSON con el estado actual de la base de datos para poder
planear una migración de datos desde el Excel consolidado.

USO EN PRODUCCIÓN:
    cd /opt/sistema_pevi
    source venv/bin/activate
    python diagnostico_pevi.py > estado_bd.json 2> diagnostico_errors.log

Luego comparte el archivo estado_bd.json (es solo metadata, sin datos sensibles
de consumo/costos — solo conteos y IDs).
"""
import os
import sys
import json
import traceback
from datetime import datetime, date
from decimal import Decimal

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from gestion.models import CentroPevi, Usuario, RegistroActividad
from auditorias.models import (
    Empresa, ProyectoAuditoria, DocumentoProyecto,
    Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano,
    OportunidadMejora,
)
from web.models import Noticia


def json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def safe(fn, default=None):
    """Ejecuta fn() y devuelve default si lanza excepción (para atributos opcionales)."""
    try:
        return fn()
    except Exception:
        return default


def main():
    out = {
        'metadata': {
            'generado_en': datetime.now().isoformat(),
            'db_name': connection.settings_dict.get('NAME'),
            'db_engine': connection.settings_dict.get('ENGINE'),
            'django_version': django.get_version(),
        },
        'centros': [],
        'usuarios': [],
        'empresas': [],
        'proyectos': [],
        'fuentes_energeticas_counts': {},
        'oportunidades_mejora': [],
        'otros_counts': {},
        'resumen': {},
        'errores': [],
    }

    # =========================================
    # CENTROS PEVI
    # =========================================
    try:
        for c in CentroPevi.objects.all().order_by('id'):
            out['centros'].append({
                'id': c.id,
                'nombre': c.nombre,
                'nombre_corto': safe(lambda: c.nombre_corto),
                'codigo_interno': safe(lambda: c.codigo_interno),
                'activo': safe(lambda: c.activo, True),
                'region': safe(lambda: c.region),
                'ciudad': safe(lambda: c.ciudad),
                'director_nombre': safe(lambda: c.director_nombre),
                'director_email': safe(lambda: c.director_email),
            })
    except Exception as e:
        out['errores'].append(f"CentroPevi: {e}\n{traceback.format_exc()}")

    # =========================================
    # USUARIOS
    # =========================================
    try:
        for u in Usuario.objects.select_related('centro_pevi').order_by('id'):
            out['usuarios'].append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'nombre_completo': f"{u.first_name} {u.last_name}".strip(),
                'rol': safe(lambda: u.rol),
                'cargo': safe(lambda: u.cargo),
                'centro_pevi_id': u.centro_pevi_id,
                'centro_pevi_nombre_corto': safe(
                    lambda: u.centro_pevi.nombre_corto if u.centro_pevi_id else None
                ),
                'is_active': u.is_active,
                'is_superuser': u.is_superuser,
                'date_joined': u.date_joined.isoformat() if u.date_joined else None,
            })
    except Exception as e:
        out['errores'].append(f"Usuario: {e}\n{traceback.format_exc()}")

    # =========================================
    # EMPRESAS
    # =========================================
    try:
        for e in Empresa.objects.select_related('centro').order_by('id'):
            out['empresas'].append({
                'id': e.id,
                'centro_id': e.centro_id,
                'centro_nombre_corto': safe(
                    lambda: e.centro.nombre_corto if e.centro_id else None
                ),
                'razon_social': e.razon_social,
                'nit': e.nit,
                'sector_productivo': e.sector_productivo,
                'ciudad': e.ciudad,
            })
    except Exception as e:
        out['errores'].append(f"Empresa: {e}\n{traceback.format_exc()}")

    # =========================================
    # PROYECTOS (con indicadores de qué fuentes energéticas tiene)
    # =========================================
    try:
        qs = (
            ProyectoAuditoria.objects
            .select_related('centro', 'empresa', 'lider_proyecto')
            .prefetch_related('equipo')
            .order_by('id')
        )
        for p in qs:
            out['proyectos'].append({
                'id': p.id,
                'nombre_proyecto': p.nombre_proyecto,
                'centro_id': p.centro_id,
                'centro_nombre_corto': safe(
                    lambda: p.centro.nombre_corto if p.centro_id else None
                ),
                'empresa_id': p.empresa_id,
                'empresa_razon_social': safe(
                    lambda: p.empresa.razon_social if p.empresa_id else None
                ),
                'empresa_nit': safe(
                    lambda: p.empresa.nit if p.empresa_id else None
                ),
                'lider_proyecto_id': p.lider_proyecto_id,
                'lider_nombre_completo': safe(
                    lambda: f"{p.lider_proyecto.first_name} {p.lider_proyecto.last_name}".strip()
                    if p.lider_proyecto_id else None
                ),
                'fase': p.fase,
                'estado': p.estado,
                'fecha_inicio': p.fecha_inicio.isoformat() if p.fecha_inicio else None,
                'fecha_cierre_estimada': (
                    p.fecha_cierre_estimada.isoformat() if p.fecha_cierre_estimada else None
                ),
                'produccion_total': p.produccion_total,
                'unidad_produccion': p.unidad_produccion,
                'equipo_ids': list(p.equipo.values_list('id', flat=True)),
                'fuentes_cargadas': {
                    'electricidad': p.electricidad_related.exists(),
                    'gas_natural': p.gasnatural_related.exists(),
                    'carbon_mineral': p.carbonmineral_related.exists(),
                    'fuel_oil': p.fueloil_related.exists(),
                    'biomasa': p.biomasa_related.exists(),
                    'gas_propano': p.gaspropano_related.exists(),
                },
                'count_opm': p.oportunidades_mejora.count(),
                'count_documentos': p.documentos.count(),
            })
    except Exception as e:
        out['errores'].append(f"ProyectoAuditoria: {e}\n{traceback.format_exc()}")

    # =========================================
    # FUENTES ENERGÉTICAS — solo conteos (no dumpeamos filas)
    # =========================================
    try:
        out['fuentes_energeticas_counts'] = {
            'electricidad': Electricidad.objects.count(),
            'gas_natural': GasNatural.objects.count(),
            'carbon_mineral': CarbonMineral.objects.count(),
            'fuel_oil': FuelOil.objects.count(),
            'biomasa': Biomasa.objects.count(),
            'gas_propano': GasPropano.objects.count(),
        }
    except Exception as e:
        out['errores'].append(f"FuentesEnergeticas counts: {e}")

    # =========================================
    # OPORTUNIDADES DE MEJORA
    # =========================================
    try:
        for o in OportunidadMejora.objects.select_related('proyecto').order_by('id'):
            out['oportunidades_mejora'].append({
                'id': o.id,
                'proyecto_id': o.proyecto_id,
                'codigo': o.codigo,
                'descripcion': (o.descripcion or '')[:120],
                'energetico': o.energetico,
            })
    except Exception as e:
        out['errores'].append(f"OportunidadMejora: {e}")

    # =========================================
    # OTROS
    # =========================================
    try:
        out['otros_counts'] = {
            'documentos_proyecto': DocumentoProyecto.objects.count(),
            'noticias': Noticia.objects.count(),
            'registro_actividad': RegistroActividad.objects.count(),
        }
    except Exception as e:
        out['errores'].append(f"Otros counts: {e}")

    # =========================================
    # RESUMEN FINAL
    # =========================================
    out['resumen'] = {
        'total_centros': len(out['centros']),
        'total_usuarios': len(out['usuarios']),
        'total_usuarios_activos': sum(1 for u in out['usuarios'] if u.get('is_active')),
        'total_empresas': len(out['empresas']),
        'total_proyectos': len(out['proyectos']),
        'total_opm': len(out['oportunidades_mejora']),
        'total_fuentes_cargadas': sum(out['fuentes_energeticas_counts'].values()),
        'hubo_errores': len(out['errores']) > 0,
    }

    json.dump(out, sys.stdout, indent=2, ensure_ascii=False, default=json_default)


if __name__ == '__main__':
    main()
