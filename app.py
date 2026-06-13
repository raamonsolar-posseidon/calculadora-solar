import os, base64, tempfile, shutil, json
from pathlib import Path
from flask import Flask, request, jsonify, Response
from motor import generar_propuesta

BASE = Path(__file__).parent
app  = Flask(__name__)
PORT = int(os.environ.get('PORT', 8080))

# ── BASE DE DATOS DE INVERSORES ──────────────────────────────────
INVERSORES_DB = {
    "SOLAX": {
        "8": {"kw": 8, "modelo": "X1-SMART-8K-G2", "tipo": "Bifásico", "eficiencia": "98.0%"},
        "10": {"kw": 10, "modelo": "X1-SMART-10K-G2", "tipo": "Bifásico", "eficiencia": "98.1%"},
        "15": {"kw": 15, "modelo": "X3-MEGA-15K-G2-LV", "tipo": "Trifásico", "eficiencia": "98.3%"},
        "20": {"kw": 20, "modelo": "X3-MEGA-20K-G2-LV", "tipo": "Trifásico", "eficiencia": "98.4%"},
        "25": {"kw": 25, "modelo": "X3-MEGA-25K-G2-LV", "tipo": "Trifásico", "eficiencia": "98.5%"},
        "30": {"kw": 30, "modelo": "X3-MEGA-30K-G2-LV", "tipo": "Trifásico", "eficiencia": "98.5%"},
        "35": {"kw": 35, "modelo": "X3-MEGA-35K-G2-LV", "tipo": "Trifásico", "eficiencia": "98.5%"},
        "50": {"kw": 50, "modelo": "X3-FORTH-50K-LV", "tipo": "Trifásico", "eficiencia": "98.6%"},
    },
    "HUAWEI": {
        "8": {"kw": 8, "modelo": "SUN2000-8KTL-M1", "tipo": "Bifásico", "eficiencia": "98.6%"},
        "10": {"kw": 10, "modelo": "SUN2000-10KTL-M1", "tipo": "Bifásico", "eficiencia": "98.6%"},
        "20": {"kw": 20, "modelo": "SUN2000-20KTL-M2", "tipo": "Trifásico", "eficiencia": "98.65%"},
    }
}

# ── TABLA DE PRECIOS (6-30 paneles) ──────────────────────────
PRECIOS = {
    6:  {'kw': 4.2,  'kwh_mes': 504,   'precio': 20_500_000},
    7:  {'kw': 4.9,  'kwh_mes': 588,   'precio': 22_500_000},
    8:  {'kw': 5.6,  'kwh_mes': 672,   'precio': 24_500_000},
    9:  {'kw': 6.3,  'kwh_mes': 756,   'precio': 25_440_000},
    10: {'kw': 7.0,  'kwh_mes': 840,   'precio': 27_360_000},
    11: {'kw': 7.7,  'kwh_mes': 924,   'precio': 29_280_000},
    12: {'kw': 8.4,  'kwh_mes': 1008,  'precio': 31_200_000},
    13: {'kw': 9.1,  'kwh_mes': 1092,  'precio': 33_120_000},
    14: {'kw': 9.8,  'kwh_mes': 1176,  'precio': 35_040_000},
    15: {'kw': 10.5, 'kwh_mes': 1260,  'precio': 36_960_000},
    16: {'kw': 11.2, 'kwh_mes': 1344,  'precio': 38_880_000},
    17: {'kw': 11.9, 'kwh_mes': 1428,  'precio': 39_100_000},
    18: {'kw': 12.6, 'kwh_mes': 1512,  'precio': 40_940_000},
    19: {'kw': 13.3, 'kwh_mes': 1596,  'precio': 42_780_000},
    20: {'kw': 14.0, 'kwh_mes': 1680,  'precio': 44_620_000},
    21: {'kw': 14.7, 'kwh_mes': 1764,  'precio': 46_460_000},
    22: {'kw': 15.4, 'kwh_mes': 1848,  'precio': 48_300_000},
    23: {'kw': 16.1, 'kwh_mes': 1932,  'precio': 50_140_000},
    24: {'kw': 16.8, 'kwh_mes': 2016,  'precio': 51_980_000},
    25: {'kw': 17.5, 'kwh_mes': 2100,  'precio': 52_065_000},
    26: {'kw': 18.2, 'kwh_mes': 2184,  'precio': 53_845_000},
    27: {'kw': 18.9, 'kwh_mes': 2268,  'precio': 55_625_000},
    28: {'kw': 19.6, 'kwh_mes': 2352,  'precio': 57_405_000},
    29: {'kw': 20.3, 'kwh_mes': 2436,  'precio': 59_185_000},
    30: {'kw': 21.0, 'kwh_mes': 2520,  'precio': 60_965_000},
}

# ── FUNCIONES DE INVERSORES AUTOMÁTICOS ──────────────────────
def calcular_rango_inversor(kw):
    """Calcula rango recomendado: 100%-140% sobredimensionamiento"""
    return {
        'min': round(kw * 1.0, 1),
        'max': round(kw * 1.4, 1),
        'recomendado': round(kw * 1.19, 1)
    }

def seleccionar_inversor_optimo(kw):
    """Retorna el kW de inversor recomendado basado en el rango"""
    rango = calcular_rango_inversor(kw)
    opciones_disponibles = [8, 10, 15, 20, 25, 30, 35, 50]
    
    mejor = None
    mejor_diff = float('inf')
    
    for opt_kw in opciones_disponibles:
        if rango['min'] <= opt_kw <= rango['max']:
            diff = abs(opt_kw - rango['recomendado'])
            if diff < mejor_diff:
                mejor_diff = diff
                mejor = opt_kw
    
    return mejor or 10

def obtener_opciones_inversor(kw_optimo):
    """Retorna las opciones de marcas disponibles para el kW recomendado"""
    kw_str = str(kw_optimo)
    opciones = []
    
    if kw_str in INVERSORES_DB["SOLAX"]:
        opciones.append({
            'marca': 'SOLAX',
            'kw': kw_optimo,
            'modelo': INVERSORES_DB["SOLAX"][kw_str]['modelo'],
            'tipo': INVERSORES_DB["SOLAX"][kw_str]['tipo']
        })
    
    if kw_str in INVERSORES_DB["HUAWEI"]:
        opciones.append({
            'marca': 'HUAWEI',
            'kw': kw_optimo,
            'modelo': INVERSORES_DB["HUAWEI"][kw_str]['modelo'],
            'tipo': INVERSORES_DB["HUAWEI"][kw_str]['tipo']
        })
    
    return opciones

# ── FUNCIONES AUXILIARES ─────────────────────────────────────
def encontrar_paneles_por_kwh(kwh_objetivo):
    """Busca automáticamente los paneles más cercanos al kWh deseado"""
    closest = 12
    min_diff = abs(PRECIOS[12]['kwh_mes'] - kwh_objetivo)
    for p, datos in PRECIOS.items():
        diff = abs(datos['kwh_mes'] - kwh_objetivo)
        if diff < min_diff:
            min_diff = diff
            closest = p
    return closest

def calcular_adicionales(paneles, adicionales):
    """Calcula el costo de los adicionales según la potencia"""
    total = 0
    if adicionales.get('acometida'):
        kw = PRECIOS[paneles]['kw']
        if kw < 8:
            total += 1_500_000
        elif kw <= 12:
            total += 2_000_000
        else:
            total += 3_000_000
    if adicionales.get('tierra'):
        total += 500_000
    if adicionales.get('estudio'):
        total += 2_000_000
    if adicionales.get('medidor'):
        total += 350_000
    return total

# ──  RUTA API: OBTENER INVERSORES AUTOMÁTICOS ──────────────────
@app.route('/api/inversores/<int:paneles>', methods=['GET'])
def api_inversores(paneles):
    """Retorna las opciones de inversores para una cantidad de paneles"""
    if paneles not in PRECIOS:
        return jsonify({'error': 'Paneles inválidos'}), 400
    
    kw_sistema = PRECIOS[paneles]['kw']
    kw_optimo = seleccionar_inversor_optimo(kw_sistema)
    opciones = obtener_opciones_inversor(kw_optimo)
    rango = calcular_rango_inversor(kw_sistema)
    
    return jsonify({
        'ok': True,
        'paneles': paneles,
        'kw_sistema': kw_sistema,
        'rango': rango,
        'inversor_recomendado_kw': kw_optimo,
        'opciones': opciones
    })
# ── HTML PRINCIPAL ──────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RA-AMON SOLAR · Generador de Propuestas</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--gold:#F5C518;--gold2:#c9a00f;--dark:#0e0d0d;--dark2:#1a1818;--dark3:#242222;--dark4:#2e2c2c;--light:#f0ede8;--muted:#7a7570;--green:#34c77b;--r:6px}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--dark);color:var(--light);font-family:'Outfit',sans-serif;min-height:100vh;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;z-index:0;background-image:linear-gradient(rgba(245,197,24,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(245,197,24,.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}
body::after{content:'';position:fixed;inset:0;z-index:0;background:radial-gradient(ellipse 55% 35% at 85% 15%,rgba(245,197,24,.05) 0%,transparent 60%),radial-gradient(ellipse 40% 50% at 5% 85%,rgba(245,197,24,.03) 0%,transparent 55%);pointer-events:none}
.wrap{position:relative;z-index:1;max-width:740px;margin:0 auto;padding:52px 24px 80px}
.hdr{display:flex;align-items:flex-start;gap:20px;margin-bottom:48px;animation:dn .5s ease both}
.bolt{width:56px;height:56px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:3px;box-shadow:0 0 28px rgba(245,197,24,.20)}
.bolt svg{width:28px;height:28px;fill:var(--dark)}
.hdr h1{font-family:'Bebas Neue',sans-serif;font-size:clamp(34px,6.5vw,52px);letter-spacing:2px;line-height:1}
.hdr h1 span{color:var(--gold)}
.hdr p{color:var(--muted);font-size:13.5px;margin-top:7px;font-weight:300}
.divider{width:100%;height:1px;background:linear-gradient(90deg,var(--gold) 0%,transparent 55%);margin-bottom:36px}
.card{background:var(--dark2);border:1px solid rgba(245,197,24,.10);border-radius:12px;padding:30px 34px;margin-bottom:16px;animation:up .45s ease both}
.card:nth-child(2){animation-delay:.05s}.card:nth-child(3){animation-delay:.10s}.card:nth-child(4){animation-delay:.15s}.card:nth-child(5){animation-delay:.20s}
.ct{font-family:'Bebas Neue',sans-serif;font-size:15px;letter-spacing:2.5px;color:var(--gold);margin-bottom:22px;display:flex;align-items:center;gap:10px}
.ct::after{content:'';flex:1;height:1px;background:rgba(245,197,24,.14)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.s2{grid-column:1/-1}
.f{display:flex;flex-direction:column;gap:7px}
.f label{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted)}
.f input,.f select{background:var(--dark3);border:1.5px solid rgba(255,255,255,.07);border-radius:var(--r);padding:13px 16px;font-family:'Outfit',sans-serif;font-size:15px;color:var(--light);outline:none;transition:border-color .18s,box-shadow .18s;appearance:none;-webkit-appearance:none}
.f select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%237a7570' stroke-width='1.5' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:40px}
.f input:focus,.f select:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(245,197,24,.09)}
.f input::placeholder{color:#3e3c3a}
.f small{color:var(--muted);font-size:11.5px}
.popts{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.po{background:var(--dark3);border:1.5px solid rgba(255,255,255,.07);border-radius:var(--r);padding:11px 4px 9px;text-align:center;cursor:pointer;transition:all .14s;color:var(--muted);font-family:'Outfit',sans-serif;font-size:11.5px;font-weight:600;user-select:none}
.po .n{display:block;font-size:20px;font-weight:700;color:var(--light);line-height:1.15;margin-bottom:1px}
.po:hover{border-color:rgba(245,197,24,.35)}
.po.on{background:rgba(245,197,24,.11);border-color:var(--gold);color:var(--gold)}
.po.on .n{color:var(--gold)}
.checkbox-group{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.checkbox-item{display:flex;align-items:flex-start;gap:10px}
.checkbox-item input{width:20px;height:20px;margin-top:2px;cursor:pointer;accent-color:var(--gold)}
.checkbox-item label{cursor:pointer;flex:1}
.checkbox-item label .title{font-weight:600;color:var(--light);font-size:12px}
.checkbox-item label .desc{color:var(--muted);font-size:10px;margin-top:2px}
.inv-opt{background:var(--dark3);border:1.5px solid rgba(245,197,24,.15);border-radius:var(--r);padding:16px;cursor:pointer;transition:all .18s;text-align:center}
.inv-opt:hover{border-color:var(--gold);background:rgba(245,197,24,.08)}
.inv-opt.selected{border-color:var(--gold);background:rgba(245,197,24,.11)}
.inv-opt .marca{font-weight:700;font-size:13px;color:var(--gold);margin-bottom:4px}
.inv-opt .modelo{font-size:11px;color:var(--light);margin-bottom:6px}
.inv-opt .tipo{font-size:10px;color:var(--muted)}
.inv-selected{background:rgba(52,199,123,.08);border:1.5px solid rgba(52,199,123,.3);border-radius:var(--r);padding:14px 16px;display:none}
.inv-selected.show{display:block}
.inv-selected .check{font-size:20px;margin-bottom:6px}
.inv-selected .info{font-size:12px;color:var(--light);font-weight:600}
.prev{background:var(--dark2);border:1px solid rgba(245,197,24,.10);border-radius:12px;padding:24px 34px;margin-bottom:16px;display:none;animation:up .35s ease both}
.prev.show{display:block}
.pl{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:16px}
.pg{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.pi{background:var(--dark3);border-radius:var(--r);padding:12px 14px}
.pi .l{font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.pi .v{font-size:13.5px;font-weight:600;color:var(--light)}
.pi .v.g{color:var(--gold)}
.cg{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}
.ci{background:var(--dark4);border-radius:var(--r);padding:10px 8px;text-align:center}
.ci .cl{font-size:9px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.ci .cv{font-size:13px;font-weight:700;color:var(--gold)}
.tip{font-size:12.5px;color:var(--muted);padding:11px 16px;margin-bottom:16px;background:rgba(245,197,24,.04);border:1px solid rgba(245,197,24,.12);border-radius:var(--r);line-height:1.6}
.tip strong{color:var(--gold)}
.btn-gen{width:100%;background:var(--gold);color:var(--dark);border:none;border-radius:var(--r);padding:19px;font-family:'Bebas Neue',sans-serif;font-size:21px;letter-spacing:3px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:12px;transition:all .18s;margin-bottom:16px;animation:up .45s .18s ease both}
.btn-gen:hover:not(:disabled){background:#ffd63a;transform:translateY(-2px);box-shadow:0 10px 28px rgba(245,197,24,.24)}
.btn-gen:disabled{opacity:.42;cursor:not-allowed;transform:none!important}
.btn-gen svg{width:22px;height:22px;fill:currentColor}
.sw{background:var(--dark2);border:1px solid rgba(245,197,24,.10);border-radius:12px;padding:26px 34px;display:none;animation:up .3s ease both}
.sw.show{display:block}
.sh{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.si{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.si.ld{background:rgba(245,197,24,.08);border:1.5px solid rgba(245,197,24,.22)}
.si.ok{background:rgba(52,199,123,.12);border:1.5px solid rgba(52,199,123,.38)}
.si.er{background:rgba(220,80,80,.12);border:1.5px solid rgba(220,80,80,.38)}
.spinner{width:20px;height:20px;border:2.5px solid rgba(245,197,24,.18);border-top-color:var(--gold);border-radius:50%;animation:spin .75s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes dn{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:translateY(0)}}
.st strong{display:block;font-size:15.5px;font-weight:600;margin-bottom:3px}
.st p{font-size:13px;color:var(--muted);line-height:1.55}
.pw{background:var(--dark3);border-radius:100px;height:5px;overflow:hidden;margin:14px 0}
.pb{background:var(--gold);height:100%;width:0%;transition:width .3s}
.steps{display:flex;flex-direction:column;gap:8px;margin:14px 0}
.stp{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:8px}
.stp .dot{width:8px;height:8px;border-radius:50%;background:rgba(245,197,24,.3);transition:all .3s}
.stp.done .dot{background:var(--green);box-shadow:0 0 8px rgba(52,199,123,.4)}
.stp.active .dot{background:var(--gold);box-shadow:0 0 10px rgba(245,197,24,.5)}
.dl{display:none}
.dl.show{display:block}
.sb{background:rgba(52,199,123,.08);border-left:3px solid var(--green);padding:16px 14px;margin-bottom:12px;border-radius:4px;font-size:12px;line-height:1.6;color:var(--light)}
.btn-dl,.btn-new{width:100%;background:var(--green);color:var(--dark);border:none;border-radius:var(--r);padding:15px;font-family:'Bebas Neue',sans-serif;font-size:16px;letter-spacing:2px;cursor:pointer;transition:all .18s;margin-bottom:8px}
.btn-dl:hover,.btn-new:hover{background:#3adb8d;transform:translateY(-2px)}
.btn-new{background:var(--dark3);color:var(--light);border:1.5px solid rgba(245,197,24,.2)}
.btn-new:hover{border-color:var(--gold);background:rgba(245,197,24,.08)}
.footer{margin-top:48px;padding:24px 0;border-top:1px solid rgba(245,197,24,.1);font-size:11px;color:var(--muted);text-align:center;line-height:1.8;animation:up .5s .4s ease both}
</style>
</head>
<body>
<div class="wrap">
<div class="hdr">
  <div class="bolt">
    <svg viewBox="0 0 24 24"><path d="M13 2H11v9H2v2h9v9h2v-9h9v-2h-9V2z"/></svg>
  </div>
  <div>
    <h1>RA-AMON <span>SOLAR</span></h1>
    <p>Generador de Propuestas de Energía Solar Fotovoltaica</p>
  </div>
</div>
<div class="divider"></div>

<div class="card">
  <div class="ct">01 · Cliente & Paneles</div>
  <div class="f">
    <label>Nombre del cliente</label>
    <input id="f-cli" type="text" placeholder="Ej: Empresa XYZ S.A.S" oninput="upPrev()">
  </div>
  <div style="margin:14px 0"></div>
  <label style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);">Cantidad de paneles</label>
  <div id="panel-opts" class="popts"></div>
  <div style="margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:14px">
    <div class="f">
      <label>O buscar por kWh/mes</label>
      <input id="f-kwh" type="number" placeholder="Ej: 1000" oninput="buscarPorKwh()">
      <small>Detecta paneles automáticamente</small>
    </div>
  </div>
</div>

<div class="card">
  <div class="ct">02 · Adicionales</div>
  <div class="checkbox-group">
    <div class="checkbox-item">
      <input type="checkbox" id="check-acometida" onchange="upPrev()">
      <label for="check-acometida">
        <div class="title">Cambio de acometida</div>
        <div class="desc" id="desc-acometida">+$2.000.000</div>
      </label>
    </div>
    <div class="checkbox-item">
      <input type="checkbox" id="check-tierra" onchange="upPrev()">
      <label for="check-tierra">
        <div class="title">Puesta a tierra</div>
        <div class="desc">+$500.000</div>
      </label>
    </div>
    <div class="checkbox-item">
      <input type="checkbox" id="check-estudio" onchange="upPrev()">
      <label for="check-estudio">
        <div class="title">Estudio conexión</div>
        <div class="desc">+$2.000.000</div>
      </label>
    </div>
    <div class="checkbox-item">
      <input type="checkbox" id="check-medidor" onchange="upPrev()">
      <label for="check-medidor">
        <div class="title">Cambio medidor</div>
        <div class="desc">+$350.000</div>
      </label>
    </div>
  </div>

  <div style="margin:14px 0"></div>
  <div class="f">
    <label>Precio total del proyecto (COP)</label>
    <input id="f-pre" type="text" readonly placeholder="Calculado automáticamente">
    <small>Se calcula automáticamente según paneles y adicionales</small>
  </div>
</div>

<div class="card">
  <div class="ct">03 · Inversor Automático ⚡</div>
  <div class="f s2" style="margin-bottom:14px">
    <label>TIPO DE SISTEMA</label>
    <select id="f-tipo-sistema" onchange="onSistemaChange()">
      <option value="ongrid" selected>On-Grid (Sin Batería) - Recomendado</option>
      <option value="hibrido" disabled>Híbrido (Con Batería) - Próximamente</option>
    </select>
    <small style="margin-top:6px;display:block;color:var(--gold);">✓ El inversor se detecta automáticamente según la potencia</small>
  </div>
  
  <div id="inv-opciones-loading" style="text-align:center;padding:20px;color:var(--muted);font-size:13px;">
    Selecciona cantidad de paneles...
  </div>
  
  <div id="inv-opciones-container" style="display:none;margin-bottom:14px;">
    <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;">Opciones disponibles</div>
    <div id="inv-opciones" class="g2"></div>
  </div>

  <div id="inv-seleccionado" class="inv-selected">
    <div class="check">✓</div>
    <div class="info" id="inv-info-text"></div>
  </div>

  <input type="hidden" id="f-mar" value="">
  <input type="hidden" id="f-mod" value="">
  <input type="hidden" id="f-kw" value="8">
  <input type="hidden" id="f-fas" value="">
</div>

<button class="btn-gen" id="btn-gen" onclick="generar()">
  <svg viewBox="0 0 24 24"><path d="M14 2H6C4.9 2 4 2.9 4 4v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM12 11l-3 3h2v4h2v-4h2l-3-3z"/></svg>
  GENERAR PROPUESTA
</button>

<div class="sw" id="sw">
  <div class="sh">
    <div class="si ld" id="si"><div class="spinner"></div></div>
    <div class="st"><strong id="st-t">Generando propuesta...</strong><p id="st-m">Preparando datos</p></div>
  </div>
  <div class="pw"><div class="pb" id="pb"></div></div>
  <div class="steps" id="stps">
    <div class="stp" id="s1"><div class="dot"></div>Calculando análisis financiero</div>
    <div class="stp" id="s2"><div class="dot"></div>Generando gráficas de proyección</div>
    <div class="stp" id="s3"><div class="dot"></div>Ensamblando presentación</div>
    <div class="stp" id="s4"><div class="dot"></div>Preparando archivo para descarga</div>
  </div>
  <div class="dl" id="dl">
    <div class="sb" id="sb"></div>
    <a class="btn-dl" id="dl-link" href="#" download>⬇ DESCARGAR PROPUESTA (.PPTX)</a>
    <button class="btn-new" onclick="resetApp()">↩ Generar otra propuesta</button>
  </div>
</div>

<div class="prev" id="prev">
  <div class="pl">Vista previa del proyecto</div>
  <div class="pg">
    <div class="pi"><div class="l">Cliente</div><div class="v" id="pv-c">—</div></div>
    <div class="pi"><div class="l">Cantidad</div><div class="v" id="pv-p">—</div></div>
    <div class="pi"><div class="l">Potencia</div><div class="v" id="pv-k">—</div></div>
    <div class="pi"><div class="l">Generación</div><div class="v" id="pv-g">—</div></div>
    <div class="pi"><div class="l">Inversor</div><div class="v" id="pv-i">—</div></div>
    <div class="pi"><div class="l">Precio total</div><div class="v g" id="pv-pr">—</div></div>
  </div>
  <div id="cg" class="cg" style="display:none">
    <div class="ci"><div class="cl">Payback</div><div class="cv" id="cv-pb">—</div></div>
    <div class="ci"><div class="cl">Ahorro 1er año</div><div class="cv" id="cv-a1">—</div></div>
    <div class="ci"><div class="cl">Ahorro 20 años</div><div class="cv" id="cv-a2">—</div></div>
    <div class="ci"><div class="cl">TIR</div><div class="cv" id="cv-ti">—</div></div>
  </div>
</div>

<div class="footer">
  <span>RA-AMON SOLAR</span> · Paneles AE Solar TopCon 700W Bifaciales<br>
  raamonsolar@gmail.com · 3128370064 · 3224235739
</div>
</div>

<script>
let pan=12, invMarcaSeleccionada='', invKwSeleccionado=8;
const precios={6:{kw:4.2,kwh:504,precio:20500000},7:{kw:4.9,kwh:588,precio:22500000},8:{kw:5.6,kwh:672,precio:24500000},9:{kw:6.3,kwh:756,precio:25440000},10:{kw:7.0,kwh:840,precio:27360000},11:{kw:7.7,kwh:924,precio:29280000},12:{kw:8.4,kwh:1008,precio:31200000},13:{kw:9.1,kwh:1092,precio:33120000},14:{kw:9.8,kwh:1176,precio:35040000},15:{kw:10.5,kwh:1260,precio:36960000},16:{kw:11.2,kwh:1344,precio:38880000},17:{kw:11.9,kwh:1428,precio:39100000},18:{kw:12.6,kwh:1512,precio:40940000},19:{kw:13.3,kwh:1596,precio:42780000},20:{kw:14.0,kwh:1680,precio:44620000},21:{kw:14.7,kwh:1764,precio:46460000},22:{kw:15.4,kwh:1848,precio:48300000},23:{kw:16.1,kwh:1932,precio:50140000},24:{kw:16.8,kwh:2016,precio:51980000},25:{kw:17.5,kwh:2100,precio:52065000},26:{kw:18.2,kwh:2184,precio:53845000},27:{kw:18.9,kwh:2268,precio:55625000},28:{kw:19.6,kwh:2352,precio:57405000},29:{kw:20.3,kwh:2436,precio:59185000},30:{kw:21.0,kwh:2520,precio:60965000}};
const $=id=>document.getElementById(id);
const fmt=n=>'$ '+Math.round(n).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');
const delay=ms=>new Promise(r=>setTimeout(r,ms));

// Crear botones de paneles
function initPanelButtons(){
  const opts=$('panel-opts');
  for(let p=6;p<=30;p+=2){
    const div=document.createElement('div');
    div.className='po'+(p===12?' on':'');
    div.innerHTML=`<span class="n">${p}</span>paneles`;
    div.onclick=()=>setPaneles(p,div);
    opts.appendChild(div);
  }
}

function setPaneles(p,btn){
  document.querySelectorAll('#panel-opts .po').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  pan=p;
  $('f-kwh').value='';
  cargarInversores();
  upPrev();
}

function buscarPorKwh(){
  const kwh=parseInt($('f-kwh').value)||0;
  if(kwh<500)return;
  let closest=12,diff=Math.abs(precios[12].kwh-kwh);
  for(const p in precios){
    const d=Math.abs(precios[p].kwh-kwh);
    if(d<diff){diff=d;closest=parseInt(p);}
  }
  pan=closest;
  const botones=document.querySelectorAll('#panel-opts .po');
  botones.forEach((b,i)=>b.classList.remove('on'));
  for(let p=6,i=0;p<=30;p+=2,i++){
    if(p===closest)botones[i].classList.add('on');
  }
  cargarInversores();
  upPrev();
}

// Cargar inversores automáticamente
async function cargarInversores(){
  try{
    const resp=await fetch(`/api/inversores/${pan}`);
    const data=await resp.json();
    if(!data.ok)throw new Error('Error cargando inversores');
    
    mostrarOpcionesInversor(data.opciones, data.inversor_recomendado_kw);
  }catch(e){
    console.error('Error:', e);
  }
}

function mostrarOpcionesInversor(opciones, kwRecomendado){
  const container=$('inv-opciones-container');
  const loading=$('inv-opciones-loading');
  const opcionesDiv=$('inv-opciones');
  
  opcionesDiv.innerHTML='';
  
  if(opciones.length===0){
    loading.textContent='No hay inversores disponibles para esta potencia';
    container.style.display='none';
    return;
  }
  
  loading.style.display='none';
  container.style.display='block';
  
  opciones.forEach(opt=>{
    const div=document.createElement('div');
    div.className='inv-opt';
    div.innerHTML=`
      <div class="marca">${opt.marca}</div>
      <div class="modelo">${opt.modelo}</div>
      <div class="tipo">${opt.tipo} · ${opt.kw}kW</div>
    `;
    div.onclick=()=>seleccionarInversor(opt, div);
    opcionesDiv.appendChild(div);
  });
  
  // Seleccionar el primero por defecto
  if(opciones.length>0){
    const primerOpt=opcionesDiv.firstChild;
    seleccionarInversor(opciones[0], primerOpt);
  }
}

function seleccionarInversor(opt, element){
  document.querySelectorAll('.inv-opt').forEach(e=>e.classList.remove('selected'));
  element.classList.add('selected');
  
  invMarcaSeleccionada=opt.marca;
  invKwSeleccionado=opt.kw;
  
  $('f-mar').value=opt.marca;
  $('f-mod').value=opt.modelo;
  $('f-kw').value=opt.kw;
  $('f-fas').value=opt.tipo;
  
  const infDiv=$('inv-seleccionado');
  infDiv.classList.add('show');
  $('inv-info-text').textContent=`${opt.marca} ${opt.modelo} (${opt.kw}kW · ${opt.tipo})`;
  
  upPrev();
}

function onSistemaChange(){
  const tipo=$('f-tipo-sistema').value;
  // Por ahora solo On-Grid está disponible
}

function calcAdicionales(){
  const ad={acometida:$('check-acometida').checked,tierra:$('check-tierra').checked,estudio:$('check-estudio').checked,medidor:$('check-medidor').checked};
  let add=0;
  if(ad.acometida){
    const kw=precios[pan].kw;
    add+=kw<8?1500000:(kw<=12?2000000:3000000);
  }
  if(ad.tierra)add+=500000;
  if(ad.estudio)add+=2000000;
  if(ad.medidor)add+=350000;
  return add;
}

function upPrev(){
  const c=$('f-cli').value.trim(),kw=precios[pan]?.kw||0,kwh=precios[pan]?.kwh||0,base=precios[pan]?.precio||0,ad=calcAdicionales(),pr=base+ad;
  const m=$('f-mar').value,mod=$('f-mod').value.trim(),invkw=$('f-kw').value,fa=$('f-fas').value;
  
  if(precios[pan]){
    const kw=precios[pan].kw;
    const acost=kw<8?'1.5M':(kw<=12?'2M':'3M');
    $('desc-acometida').textContent='+$'+acost;
  }
  
  $('f-pre').value=fmt(pr);
  const pv=$('prev');
  if(!c&&!kw&&!pr){pv.classList.remove('show');return;}
  pv.classList.add('show');
  $('pv-c').textContent=c.toUpperCase()||'—';
  $('pv-p').textContent=pan>0?`${pan} paneles`:'—';
  $('pv-k').textContent=kw>0?`${kw} kW`:'—';
  $('pv-g').textContent=kwh>0?`${kwh.toLocaleString('es-CO')} kWh`:'—';
  $('pv-i').textContent=mod?`${m} ${mod} (${invkw}kW)`:'—';
  $('pv-pr').textContent=pr>0?fmt(pr):'—';
  const cg=$('cg');
  if(pan>0&&pr>1000000){
    cg.style.display='grid';
    const d=calc(pan,pr);
    $('cv-pb').textContent=`~ ${d.pb.toFixed(1)} años`;
    $('cv-a1').textContent=fmt(d.a1);
    $('cv-a2').textContent=fmt(d.a20);
    $('cv-ti').textContent=`${d.tir.toFixed(1)}%`;
  }
}

function calc(p,pr){
  const kw=precios[p].kw,kwh=precios[p].kwh,m=12,ahorro_m=kwh*1200,ahorro_a=ahorro_m*m;
  let pb=null;
  const fl=[];
  for(let i=0;i<20;i++)fl.push(ahorro_a);
  let a=-pr;
  for(let i=0;i<fl.length;i++){const pv=a;a+=fl[i];if(a>=0){pb=i+(-pv/fl[i]);break;}}
  const a20=fl.reduce((s,f)=>s+f,0);
  let lo=0,hi=5;
  for(let j=0;j<200;j++){const m=(lo+hi)/2;const n=-pr+fl.reduce((s,f,i)=>s+f/Math.pow(1+m,i+1),0);if(n>0)lo=m;else hi=m;}
  return{a20,pb,tir:(lo+hi)/2*100,a1:fl[0]};
}

function step(n){
  for(let i=1;i<=4;i++){const e=$(`s${i}`);e.classList.remove('active','done');if(i<n)e.classList.add('done');else if(i===n)e.classList.add('active');}
  $('pb').style.width=`${Math.round((n-1)/4*100)}%`;
}

async function generar(){
  const cli=$('f-cli').value.trim(),pr=parseInt($('f-pre').value.replace(/\D/g,''))||0;
  const mar=$('f-mar').value,mod=$('f-mod').value.trim()||'MODELO',kw=$('f-kw').value,fas=$('f-fas').value;
  if(!cli){alert('Ingresa el nombre del cliente.');return;}
  if(!pan||pan<6||pan>30){alert('Selecciona cantidad de paneles válida.');return;}
  if(!mar){alert('Selecciona un inversor.');return;}
  if(pr<1000000){alert('Ingresa un precio válido (mín. $1.000.000).');return;}

  $('btn-gen').disabled=true;
  $('sw').classList.add('show');
  $('dl').classList.remove('show');
  $('stps').style.display='flex';
  $('si').className='si ld';$('si').innerHTML='<div class="spinner"></div>';
  $('st-t').textContent='Generando propuesta...';
  $('st-m').textContent=`${cli.toUpperCase()} · ${pan} paneles · ${fmt(pr)}`;
  step(1);

  try{
    await delay(200);step(2);$('st-m').textContent='Generando gráficas financieras...';
    await delay(300);step(3);$('st-m').textContent='Ensamblando diapositivas...';

    const resp=await fetch('/generar',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({nombre:cli,paneles:pan,precio:pr,inv_marca:mar,inv_modelo:mod,inv_kw:parseInt(kw),inv_fase:fas})
    });

    await delay(200);step(4);$('st-m').textContent='Preparando descarga...';

    if(!resp.ok){
      const err=await resp.json();
      throw new Error(err.error||'Error del servidor');
    }

    const data=await resp.json();
    if(!data.ok)throw new Error(data.error||'Error generando el archivo');

    const bytes=Uint8Array.from(atob(data.data),c=>c.charCodeAt(0));
    const blob=new Blob([bytes],{type:'application/vnd.openxmlformats-officedocument.presentationml
