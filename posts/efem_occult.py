#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Efemérides de Occult  ->  Excel estructurado
============================================
Convierte el archivo de texto plano "Diary of Astronomical Phenomena"
generado por Occult 4.x en un libro de Excel de consulta fácil.

USO BÁSICO
----------
    python efemerides_a_excel.py efemerides_2026.txt

Genera "Efemerides_2026.xlsx" en la misma carpeta del archivo de entrada.

OPCIONES
--------
    -o, --salida ARCHIVO    nombre del .xlsx de salida
    --anio AAAA             año, si no se detecta en el encabezado
    --utc HORAS             desplazamiento horario local (defecto -5, Colombia)
    --csv                   además exporta un CSV plano (UTF-8 con BOM)
    -q, --silencioso        no imprime el informe

HOJAS QUE PRODUCE
-----------------
    Efemérides      tabla completa, con autofiltro y paneles congelados
    Resumen         indicadores y matriz categoría x mes (fórmulas COUNTIFS)
    Destacados      eclipses, oposiciones, elongaciones, estaciones
    Ocultaciones    solo las ocultaciones lunares
    Fases lunares   para planificar noches oscuras

Requiere: openpyxl   ->   pip install openpyxl
"""

import argparse
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, time

# En Windows la consola suele ser cp1252 y no admite algunos caracteres.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import FormulaRule
except ImportError:
    sys.exit("ERROR: falta openpyxl.  Instalalo con:  pip install openpyxl")


# ===========================================================================
# 1. TABLAS DE REFERENCIA
# ===========================================================================

MESES_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December']
MESES_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
            'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
DIAS_ES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

OBJETOS = {
    'Moon': 'Luna', 'Sun': 'Sol', 'Earth': 'Tierra',
    'Mercury': 'Mercurio', 'Venus': 'Venus', 'Mars': 'Marte',
    'Jupiter': 'Júpiter', 'Saturn': 'Saturno', 'Uranus': 'Urano',
    'Neptune': 'Neptuno', 'Pluto': 'Plutón',
    # estrellas brillantes del zodiaco que la Luna puede ocultar
    'Pollux': 'Pólux', 'Regulus': 'Régulo', 'Spica': 'Spica',
    'Antares': 'Antares', 'Aldebaran': 'Aldebarán',
}

CATEGORIAS = ['Fase lunar', 'Ocultación', 'Aproximación', 'Oposición',
              'Conjunción solar', 'Elongación', 'Estacionario', 'Órbita lunar',
              'Declinación lunar', 'Órbita terrestre', 'Estación', 'Tránsito',
              'Otro']

FASES = {'NEW MOON': 'Luna nueva', 'FULL MOON': 'Luna llena',
         'FIRST QUARTER': 'Cuarto creciente', 'LAST QUARTER': 'Cuarto menguante'}


def tr(nombre):
    """Traduce el nombre de un objeto; si no está en la tabla lo deja igual."""
    return OBJETOS.get(nombre, nombre)


def con_articulo(nombre):
    """Devuelve 'la Luna', 'el Sol'... para que la frase concuerde."""
    if nombre in ('Luna', 'Tierra'):
        return 'la ' + nombre
    if nombre == 'Sol':
        return 'el Sol'
    return nombre


# ===========================================================================
# 2. LECTURA DEL ARCHIVO
# ===========================================================================

def detectar_anio(texto):
    """Busca el año en el encabezado 'Diary of Astronomical Phenomena AAAA'."""
    m = re.search(r'Diary of Astronomical Phenomena\s+(\d{4})', texto)
    if m:
        return int(m.group(1))
    m = re.search(r'\b(19|20|21)\d{2}\b', texto[:400])
    return int(m.group(0)) if m else None


def leer_efemerides(ruta, anio=None):
    """Parsea el archivo. Devuelve (registros, anio, lineas_no_parseadas)."""
    with open(ruta, encoding='utf-8', errors='replace') as fh:
        texto = fh.read()

    if anio is None:
        anio = detectar_anio(texto)
        if anio is None:
            raise SystemExit(
                "ERROR: no pude detectar el año en el archivo.\n"
                "       Indicalo a mano, por ejemplo:  --anio 2026")

    registros = []
    no_parseadas = []
    mes_actual = None
    corte = None

    for nlinea, linea in enumerate(texto.split('\n'), start=1):
        limpia = linea.strip()

        # cambio de mes
        if limpia in MESES_EN:
            mes_actual = MESES_EN.index(limpia) + 1
            corte = None
            continue

        # línea de encabezado " d  h ...  d  h": fija la columna de corte
        if re.match(r'^\s*d\s+h(\s|$)', linea):
            primera = linea.index('d')
            segunda = linea.find('d', primera + 1)
            corte = (segunda - 1) if segunda > 0 else None
            continue

        if mes_actual is None or not limpia:
            continue
        if 'Diary of Astronomical' in linea:
            continue

        # el formato trae dos registros por línea, uno en cada mitad
        mitades = [linea[:corte], linea[corte:]] if corte else [linea]
        for mitad in mitades:
            mitad = mitad.rstrip()
            if not mitad.strip():
                continue
            m = re.match(r'^\s*(\d{1,2})\s+(\d{1,2})\s\s+(.+)$', mitad)
            if not m:
                no_parseadas.append((nlinea, mitad.strip()))
                continue
            dia, hora, desc = int(m.group(1)), int(m.group(2)), m.group(3).strip()
            try:
                ut = datetime(anio, mes_actual, dia, hora)
            except ValueError:
                no_parseadas.append((nlinea, f"fecha inválida: {mitad.strip()}"))
                continue
            registros.append({'ut': ut, 'desc': desc})

    registros.sort(key=lambda r: r['ut'])
    return registros, anio, no_parseadas


# ===========================================================================
# 3. CLASIFICACIÓN Y TRADUCCIÓN
# ===========================================================================

def clasificar(reg):
    """Añade categoría, evento en español, objetos, separación y banderas."""
    desc = reg['desc']

    # banderas al final de la descripción
    reg['ocultacion'] = bool(re.search(r'\s+Occn\s*$', desc))
    reg['eclipse'] = bool(re.search(r'\s+Eclipse\s*$', desc))
    nucleo = re.sub(r'\s+(Occn|Eclipse)\s*$', '', desc).strip()
    nucleo = re.sub(r'\s+(Occn|Eclipse)\s*$', '', nucleo).strip()   # ambas banderas

    reg.update(categoria='Otro', evento='', obj1='', obj2='',
               separacion=None, direccion='')

    # --- aproximación / ocultación:  "Venus 2.0N of Moon"
    m = re.match(r'^(\w+)\s+([\d.]+)([NS])\s+of\s+(\w+)$', nucleo)
    if m:
        a, sep, ns, b = tr(m.group(1)), float(m.group(2)), m.group(3), tr(m.group(4))
        rumbo = 'norte' if ns == 'N' else 'sur'
        reg.update(categoria='Aproximación', obj1=a, obj2=b, separacion=sep,
                   direccion=rumbo.capitalize(),
                   evento=f"{a} a {sep:.1f}° al {rumbo} de {con_articulo(b)}")
        if reg['ocultacion']:
            reg['categoria'] = 'Ocultación'
            reg['evento'] = (f"Ocultación de {a} por {con_articulo(b)}"
                             if b == 'Luna' else
                             f"{a} a {sep:.1f}° al {rumbo} de {con_articulo(b)} (ocultación)")
        return reg

    # --- fase lunar
    if nucleo.upper() in FASES:
        reg.update(categoria='Fase lunar', obj1='Luna', evento=FASES[nucleo.upper()])
        if reg['eclipse']:
            if 'nueva' in reg['evento']:
                reg['evento'] += ' — eclipse solar'
            elif 'llena' in reg['evento']:
                reg['evento'] += ' — eclipse lunar'
        return reg

    # --- perigeo / apogeo
    m = re.match(r'^Moon at (perigee|apogee)$', nucleo)
    if m:
        t = 'perigeo' if m.group(1) == 'perigee' else 'apogeo'
        reg.update(categoria='Órbita lunar', obj1='Luna', evento=f"Luna en {t}")
        return reg

    # --- declinación extrema de la Luna
    m = re.match(r'^Moon furthest (North|South)\s*\(([-\d.]+)\)$', nucleo)
    if m:
        rumbo = 'norte' if m.group(1) == 'North' else 'sur'
        val = float(m.group(2))
        reg.update(categoria='Declinación lunar', obj1='Luna', separacion=val,
                   direccion=rumbo.capitalize(),
                   evento=f"Luna en su máxima declinación {rumbo} ({val:+.1f}°)")
        return reg

    # --- movimiento estacionario
    m = re.match(r'^(\w+) stationary$', nucleo)
    if m:
        reg.update(categoria='Estacionario', obj1=tr(m.group(1)),
                   evento=f"{tr(m.group(1))} estacionario")
        return reg

    # --- oposición
    m = re.match(r'^(\w+) at opposition$', nucleo)
    if m:
        reg.update(categoria='Oposición', obj1=tr(m.group(1)),
                   evento=f"{tr(m.group(1))} en oposición")
        return reg

    # --- conjunción con el Sol
    m = re.match(r'^(\w+) at conjunction$', nucleo)
    if m:
        reg.update(categoria='Conjunción solar', obj1=tr(m.group(1)),
                   evento=f"{tr(m.group(1))} en conjunción con el Sol")
        return reg
    m = re.match(r'^(\w+) (superior|inferior) conjunction$', nucleo)
    if m:
        reg.update(categoria='Conjunción solar', obj1=tr(m.group(1)),
                   evento=f"{tr(m.group(1))} en conjunción {m.group(2)}")
        return reg

    # --- máxima elongación
    m = re.match(r'^(\w+) greatest elong\.?\s*([EW])\s*\((\d+)\)$', nucleo)
    if m:
        lado = 'este' if m.group(2) == 'E' else 'oeste'
        val = float(m.group(3))
        reg.update(categoria='Elongación', obj1=tr(m.group(1)), separacion=val,
                   direccion=lado.capitalize(),
                   evento=f"{tr(m.group(1))} en máxima elongación {lado} ({val:.0f}°)")
        return reg

    # --- máximo brillo (Venus)
    m = re.match(r'^(\w+) greatest brilliancy$', nucleo)
    if m:
        reg.update(categoria='Elongación', obj1=tr(m.group(1)),
                   evento=f"{tr(m.group(1))} en su máximo brillo")
        return reg

    # --- equinoccios y solsticios
    if nucleo in ('Equinox', 'Solstice'):
        reg.update(categoria='Estación', obj1='Sol',
                   evento='Equinoccio' if nucleo == 'Equinox' else 'Solsticio')
        return reg

    # --- perihelio / afelio terrestre
    m = re.match(r'^Earth at (perihelion|aphelion)$', nucleo)
    if m:
        t = 'perihelio' if m.group(1) == 'perihelion' else 'afelio'
        reg.update(categoria='Órbita terrestre', obj1='Tierra',
                   evento=f"Tierra en {t}")
        return reg

    # --- tránsito
    m = re.match(r'^Transit of (\w+)$', nucleo)
    if m:
        reg.update(categoria='Tránsito', obj1=tr(m.group(1)),
                   evento=f"Tránsito de {tr(m.group(1))} sobre el Sol")
        return reg

    # no reconocido: se conserva el texto original
    reg['evento'] = nucleo
    return reg


# ===========================================================================
# 4. CONSTRUCCIÓN DEL EXCEL
# ===========================================================================

TIPO = 'Arial'
F_HDR = Font(name=TIPO, size=10, bold=True, color='FFFFFF')
F_BODY = Font(name=TIPO, size=10)
F_BOLD = Font(name=TIPO, size=10, bold=True)
F_TIT = Font(name=TIPO, size=14, bold=True, color='1F3864')
F_SUB = Font(name=TIPO, size=10, bold=True, color='1F3864')
F_NOTA = Font(name=TIPO, size=9, italic=True, color='595959')
FILL_HDR = PatternFill('solid', fgColor='1F3864')
FILL_TOT = PatternFill('solid', fgColor='DCE6F1')
_l = Side(style='thin', color='BFBFBF')
BORDE = Border(left=_l, right=_l, top=_l, bottom=_l)
A_CTR = Alignment(horizontal='center', vertical='center')
A_LFT = Alignment(horizontal='left', vertical='center')
A_HDR = Alignment(horizontal='center', vertical='center', wrap_text=True)

COLUMNAS = [
    ('N°', 5), ('Fecha UT', 11), ('Hora UT', 8), ('Fecha local', 11),
    ('Hora local', 9), ('Mes (UT)', 12), ('Día (UT)', 11), ('Categoría', 17),
    ('Evento', 42), ('Objeto principal', 15), ('Objeto secundario', 17),
    ('Separación (°)', 12), ('Dirección', 10), ('Ocultación', 11),
    ('Eclipse', 9), ('Texto original', 34),
]

COLS_CONSULTA = [('Fecha UT', 11, 'B'), ('Hora UT', 8, 'C'),
                 ('Fecha local', 11, 'D'), ('Hora local', 9, 'E'),
                 ('Día (UT)', 11, 'G'), ('Evento', 44, 'I')]


def _hoja_principal(wb, registros, utc):
    ws = wb.active
    ws.title = 'Efemérides'

    for c, (titulo, ancho) in enumerate(COLUMNAS, start=1):
        cel = ws.cell(row=1, column=c, value=titulo)
        cel.font, cel.fill, cel.alignment, cel.border = F_HDR, FILL_HDR, A_HDR, BORDE
        ws.column_dimensions[get_column_letter(c)].width = ancho
    ws.row_dimensions[1].height = 30

    for i, reg in enumerate(registros, start=1):
        fila = i + 1
        ut = reg['ut']
        loc = ut + timedelta(hours=utc)
        valores = [
            i, ut.date(), time(ut.hour, 0), loc.date(), time(loc.hour, 0),
            MESES_ES[ut.month - 1], DIAS_ES[ut.weekday()], reg['categoria'],
            reg['evento'], reg['obj1'], reg['obj2'], reg['separacion'],
            reg['direccion'],
            'Sí' if reg['ocultacion'] else 'No',
            'Sí' if reg['eclipse'] else 'No',
            reg['desc'],
        ]
        for c, v in enumerate(valores, start=1):
            cel = ws.cell(row=fila, column=c, value=v)
            cel.font, cel.border = F_BODY, BORDE
            cel.alignment = A_CTR if c in (1, 2, 3, 4, 5, 12, 13, 14, 15) else A_LFT
        for col in (2, 4):
            ws.cell(row=fila, column=col).number_format = 'DD/MM/YYYY'
        for col in (3, 5):
            ws.cell(row=fila, column=col).number_format = 'HH:MM'
        ws.cell(row=fila, column=12).number_format = '0.0'

    ultima = len(registros) + 1
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:P{ultima}'

    rango = f'A2:P{ultima}'
    ws.conditional_formatting.add(rango, FormulaRule(
        formula=['$O2="Sí"'], fill=PatternFill('solid', fgColor='FFF2CC')))
    ws.conditional_formatting.add(rango, FormulaRule(
        formula=['$N2="Sí"'], fill=PatternFill('solid', fgColor='E8F1FA')))
    return ultima


def _hoja_resumen(wb, anio, ultima, utc):
    rs = wb.create_sheet('Resumen')
    rs.column_dimensions['A'].width = 22
    for c in range(2, 16):
        rs.column_dimensions[get_column_letter(c)].width = 9.5

    rs['A1'] = f'Efemérides astronómicas {anio} — resumen'
    rs['A1'].font = F_TIT
    rs['A2'] = ('Fuente: Diary of Astronomical Phenomena, generado con Occult 4.x. '
                'Horas del original en Tiempo Universal.')
    rs['A2'].font = F_NOTA

    rs['A4'] = 'Indicadores'
    rs['A4'].font = F_SUB
    indicadores = [
        ('Total de eventos', f"=COUNTA(Efemérides!$I$2:$I${ultima})"),
        ('Ocultaciones', f'=COUNTIF(Efemérides!$N$2:$N${ultima},"Sí")'),
        ('Eclipses', f'=COUNTIF(Efemérides!$O$2:$O${ultima},"Sí")'),
        ('Oposiciones planetarias', f'=COUNTIF(Efemérides!$H$2:$H${ultima},"Oposición")'),
        ('Fases lunares', f'=COUNTIF(Efemérides!$H$2:$H${ultima},"Fase lunar")'),
    ]
    for i, (etiqueta, formula) in enumerate(indicadores):
        f = 5 + i
        a = rs.cell(row=f, column=1, value=etiqueta)
        a.font, a.border = F_BODY, BORDE
        b = rs.cell(row=f, column=2, value=formula)
        b.font, b.alignment, b.border = F_BOLD, A_CTR, BORDE

    tope = 12
    rs.cell(row=tope, column=1, value='Eventos por categoría y mes').font = F_SUB
    hr = tope + 1
    cel = rs.cell(row=hr, column=1, value='Categoría')
    cel.font, cel.fill, cel.alignment, cel.border = F_HDR, FILL_HDR, A_HDR, BORDE
    for j, mes in enumerate(MESES_ES):
        cel = rs.cell(row=hr, column=2 + j, value=mes)
        cel.font, cel.fill, cel.alignment, cel.border = F_HDR, FILL_HDR, A_HDR, BORDE
    cel = rs.cell(row=hr, column=14, value='Total')
    cel.font, cel.fill, cel.alignment, cel.border = F_HDR, FILL_HDR, A_HDR, BORDE
    rs.row_dimensions[hr].height = 28

    for i, cat in enumerate(CATEGORIAS):
        f = hr + 1 + i
        a = rs.cell(row=f, column=1, value=cat)
        a.font, a.border, a.alignment = F_BODY, BORDE, A_LFT
        for j in range(12):
            col = get_column_letter(2 + j)
            b = rs.cell(row=f, column=2 + j, value=(
                f'=COUNTIFS(Efemérides!$H$2:$H${ultima},$A{f},'
                f'Efemérides!$F$2:$F${ultima},{col}${hr})'))
            b.font, b.alignment, b.border = F_BODY, A_CTR, BORDE
        t = rs.cell(row=f, column=14, value=f'=SUM(B{f}:M{f})')
        t.font, t.alignment, t.border = F_BOLD, A_CTR, BORDE

    ftot = hr + 1 + len(CATEGORIAS)
    a = rs.cell(row=ftot, column=1, value='Total')
    a.font, a.border = F_BOLD, BORDE
    for j in range(12):
        col = get_column_letter(2 + j)
        b = rs.cell(row=ftot, column=2 + j,
                    value=f'=SUM({col}{hr+1}:{col}{ftot-1})')
        b.font, b.alignment, b.border, b.fill = F_BOLD, A_CTR, BORDE, FILL_TOT
    b = rs.cell(row=ftot, column=14, value=f'=SUM(B{ftot}:M{ftot})')
    b.font, b.alignment, b.border, b.fill = F_BOLD, A_CTR, BORDE, FILL_TOT

    signo = f'UTC{utc:+d}'
    notas = [
        'Notas metodológicas',
        f'• Las horas del documento original están en Tiempo Universal (UT). '
        f'La columna "Hora local" aplica {signo}; cuando el evento cae en las primeras '
        f'horas UT, la fecha local puede corresponder al día anterior.',
        '• Las horas del almanaque vienen redondeadas a la hora entera.',
        '• "Separación (°)" recoge la distancia angular de las aproximaciones, la '
        'elongación máxima y la declinación extrema en los pasos lunares.',
        '• Los eventos marcados como eclipse coinciden con luna nueva (eclipse solar) '
        'o luna llena (eclipse lunar); el tipo y la visibilidad geográfica no vienen '
        'en el archivo de origen.',
        '• "Occn" en el texto original indica ocultación por la Luna.',
        '• Los conteos son fórmulas COUNTIFS sobre la hoja Efemérides: si la editas, '
        'se recalculan.',
    ]
    for i, texto in enumerate(notas):
        cel = rs.cell(row=ftot + 3 + i, column=1, value=texto)
        cel.font = F_SUB if i == 0 else F_NOTA
        cel.alignment = Alignment(horizontal='left', vertical='top')


def _hoja_consulta(wb, nombre, subconjunto, titulo, columnas):
    sh = wb.create_sheet(nombre)
    sh['A1'] = titulo
    sh['A1'].font = F_TIT
    sh['A2'] = 'Los datos se enlazan a la hoja Efemérides y se actualizan con ella.'
    sh['A2'].font = F_NOTA
    hdr = 4
    for c, (tit, ancho, _) in enumerate(columnas, start=1):
        cel = sh.cell(row=hdr, column=c, value=tit)
        cel.font, cel.fill, cel.alignment, cel.border = F_HDR, FILL_HDR, A_HDR, BORDE
        sh.column_dimensions[get_column_letter(c)].width = ancho
    sh.row_dimensions[hdr].height = 26

    for i, reg in enumerate(subconjunto):
        f = hdr + 1 + i
        for c, (_, _, origen) in enumerate(columnas, start=1):
            cel = sh.cell(row=f, column=c,
                          value=f"='Efemérides'!{origen}{reg['_fila']}")
            cel.font, cel.border = F_BODY, BORDE
            cel.alignment = A_CTR if origen in 'BCDEL' else A_LFT
            if origen in 'BD':
                cel.number_format = 'DD/MM/YYYY'
            elif origen in 'CE':
                cel.number_format = 'HH:MM'
            elif origen == 'L':
                cel.number_format = '0.0'
    sh.freeze_panes = f'A{hdr + 1}'
    if not subconjunto:
        sh.cell(row=hdr + 1, column=1, value='(sin eventos de este tipo)').font = F_NOTA


def construir_excel(registros, anio, utc, salida):
    wb = openpyxl.Workbook()
    ultima = _hoja_principal(wb, registros, utc)
    _hoja_resumen(wb, anio, ultima, utc)

    for i, reg in enumerate(registros, start=1):
        reg['_fila'] = i + 1

    destacados = [r for r in registros
                  if r['categoria'] in ('Oposición', 'Elongación', 'Estación',
                                        'Órbita terrestre', 'Conjunción solar')
                  or r['eclipse']]
    _hoja_consulta(wb, 'Destacados', destacados,
                   f'Eventos destacados {anio} — eclipses, oposiciones, '
                   f'elongaciones y estaciones',
                   COLS_CONSULTA + [('Categoría', 17, 'H')])

    ocultaciones = [r for r in registros if r['ocultacion']]
    _hoja_consulta(wb, 'Ocultaciones', ocultaciones,
                   f'Ocultaciones lunares {anio}',
                   COLS_CONSULTA + [('Objeto ocultado', 16, 'J'),
                                    ('Separación (°)', 12, 'L')])

    fases = [r for r in registros if r['categoria'] == 'Fase lunar']
    _hoja_consulta(wb, 'Fases lunares', fases,
                   f'Fases lunares {anio} — planificación de noches oscuras',
                   COLS_CONSULTA)

    wb.save(salida)
    return {'destacados': len(destacados), 'ocultaciones': len(ocultaciones),
            'fases': len(fases)}


def exportar_csv(registros, anio, utc, ruta):
    import csv
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['n', 'fecha_ut', 'hora_ut', 'fecha_local', 'hora_local',
                    'mes', 'dia_semana', 'categoria', 'evento', 'objeto_1',
                    'objeto_2', 'separacion_grados', 'direccion', 'ocultacion',
                    'eclipse', 'texto_original'])
        for i, r in enumerate(registros, start=1):
            ut = r['ut']
            loc = ut + timedelta(hours=utc)
            w.writerow([i, ut.strftime('%Y-%m-%d'), f'{ut.hour:02d}:00',
                        loc.strftime('%Y-%m-%d'), f'{loc.hour:02d}:00',
                        MESES_ES[ut.month - 1], DIAS_ES[ut.weekday()],
                        r['categoria'], r['evento'], r['obj1'], r['obj2'],
                        '' if r['separacion'] is None else f"{r['separacion']:.1f}",
                        r['direccion'],
                        'Si' if r['ocultacion'] else 'No',
                        'Si' if r['eclipse'] else 'No', r['desc']])


# ===========================================================================
# 5. PROGRAMA PRINCIPAL
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(
        description='Convierte las efemérides de Occult a un Excel de consulta.')
    ap.add_argument('entrada', help='archivo .txt generado por Occult')
    ap.add_argument('-o', '--salida', default=None, help='archivo .xlsx de salida')
    ap.add_argument('--anio', type=int, default=None,
                    help='año, si no aparece en el encabezado')
    ap.add_argument('--utc', type=int, default=-5,
                    help='desplazamiento horario local (defecto -5, Colombia)')
    ap.add_argument('--csv', action='store_true', help='exportar también un CSV')
    ap.add_argument('-q', '--silencioso', action='store_true')
    args = ap.parse_args()

    if not os.path.isfile(args.entrada):
        sys.exit(f"ERROR: no encuentro el archivo '{args.entrada}'")

    registros, anio, no_parseadas = leer_efemerides(args.entrada, args.anio)
    if not registros:
        sys.exit("ERROR: no se extrajo ningún evento. ¿Es el formato de Occult?")

    for reg in registros:
        clasificar(reg)

    salida = args.salida or os.path.join(
        os.path.dirname(os.path.abspath(args.entrada)) or '.',
        f'Efemerides_{anio}.xlsx')

    conteos = construir_excel(registros, anio, args.utc, salida)

    ruta_csv = None
    if args.csv:
        ruta_csv = os.path.splitext(salida)[0] + '.csv'
        exportar_csv(registros, anio, args.utc, ruta_csv)

    if args.silencioso:
        return

    # ---------------------------------------------------------- informe
    print()
    print(f"  Año detectado ......... {anio}")
    print(f"  Eventos procesados .... {len(registros)}")
    print(f"  Hora local ............ UTC{args.utc:+d}")
    print()
    print("  Por categoría:")
    cuenta = Counter(r['categoria'] for r in registros)
    for cat in CATEGORIAS:
        if cuenta.get(cat):
            print(f"    {cat:<20} {cuenta[cat]:>4}")
    print()
    print(f"  Ocultaciones .......... {conteos['ocultaciones']}")
    print(f"  Eclipses .............. {sum(r['eclipse'] for r in registros)}")
    print(f"  Destacados ............ {conteos['destacados']}")
    print(f"  Fases lunares ......... {conteos['fases']}")
    print()
    print(f"  Excel guardado en:\n    {salida}")
    if ruta_csv:
        print(f"  CSV guardado en:\n    {ruta_csv}")

    otros = [r for r in registros if r['categoria'] == 'Otro']
    if otros:
        print()
        print(f"  AVISO: {len(otros)} evento(s) sin clasificar (se conservan con su")
        print("         texto original; revisa si conviene añadir un patrón):")
        for r in otros[:15]:
            print(f"    {r['ut']:%d/%m %H}h  {r['desc']}")
        if len(otros) > 15:
            print(f"    ... y {len(otros) - 15} más")

    if no_parseadas:
        print()
        print(f"  AVISO: {len(no_parseadas)} fragmento(s) de línea no interpretados:")
        for nl, txt in no_parseadas[:10]:
            print(f"    línea {nl}: {txt[:60]}")
        if len(no_parseadas) > 10:
            print(f"    ... y {len(no_parseadas) - 10} más")
    print()


if __name__ == '__main__':
    main()