from flask import Flask

app = Flask(__name__)
<<<<<<< HEAD

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>RA-AMON SOLAR</title>
        <style>
            body { background: #0e0d0d; color: #f0ede8; font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #F5C518; }
            input { padding: 10px; margin: 10px; }
            button { background: #F5C518; color: #0e0d0d; padding: 10px 20px; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>? RA-AMON SOLAR</h1>
        <p>Generador de Propuestas Fotovoltaicas</p>
        <form>
            <input type="text" placeholder="Nombre del Cliente" required>
            <input type="number" placeholder="N�mero de Paneles" required>
            <button type="submit">Generar Propuesta</button>
        </form>
    </body>
    </html>
    '''
=======
CORS(app)

# ========== DATABASE ==========
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///propuestas.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Propuesta(db.Model):
    __tablename__ = 'propuestas'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre_cliente = db.Column(db.String(255))
    paneles = db.Column(db.Integer)
    precio = db.Column(db.Float)
    inversor_marca = db.Column(db.String(100))
    inversor_modelo = db.Column(db.String(100))
    inversor_kw = db.Column(db.Float)
    inversor_fase = db.Column(db.String(50))
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_primer_acceso = db.Column(db.DateTime)
    estado = db.Column(db.String(50), default='pendiente')
    
    visualizaciones = db.relationship('Visualizacion', backref='propuesta', cascade='all, delete-orphan')
    eventos = db.relationship('Evento', backref='propuesta', cascade='all, delete-orphan')

class Visualizacion(db.Model):
    __tablename__ = 'visualizaciones'
    id = db.Column(db.Integer, primary_key=True)
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    duracion_segundos = db.Column(db.Integer, default=0)

class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'))
    tipo = db.Column(db.String(50))
    seccion = db.Column(db.String(100))
    valor = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

DARK_BG = '#0c0b0b'
GOLD = '#F5C518'
WHITE = '#f0ede8'
MUTED = '#9a9590'
BLUE_BAR = '#1e55a0'

def fmt(n):
    return f"$ {int(round(n)):,}".replace(",", ".")

def calcular(inversion, paneles, gen_mensual, tarifa=1000, inflacion=0.08, degradacion=0.005, mant_panel=25000, aÃ±os=20):
    mant_anual = paneles * mant_panel * 2
    flujos, acums, acum = [], [], -inversion
    for i in range(1, aÃ±os+1):
        g = gen_mensual * 12 * (1-degradacion)**(i-1)
        t = tarifa * (1+inflacion)**(i-1)
        f = g*t - mant_anual
        acum += f
        flujos.append(f)
        acums.append(acum)
    
    acum_tmp, payback = -inversion, aÃ±os
    for i, f in enumerate(flujos):
        prev = acum_tmp
        acum_tmp += f
        if acum_tmp >= 0:
            payback = i + (-prev/f)
            break
    
    ahorro20 = sum(flujos)
    van = -inversion + sum(f/(1.12)**i for i,f in enumerate(flujos,1))
    lo, hi = 0.0, 5.0
    for _ in range(200):
        m = (lo+hi)/2
        npv = -inversion + sum(f/(1+m)**i for i,f in enumerate(flujos,1))
        if npv > 0:
            lo = m
        else:
            hi = m
    tir = (lo+hi)/2
    bc = sum(f/(1.12)**i for i,f in enumerate(flujos,1)) / inversion
    
    return {
        'flujos': flujos,
        'acums': acums,
        'payback': payback,
        'ahorro1': flujos[0],
        'ahorro20': ahorro20,
        'van': van,
        'tir': tir*100,
        'bc': bc,
        'roi20': ahorro20/inversion*100,
        'roi_anual': ahorro20/inversion*100/aÃ±os,
        'mant_anual': mant_anual
    }

@app.route('/')
def index():
    return render_template('formulario.html')

@app.route('/api/crear-propuesta', methods=['POST'])
def crear_propuesta():
    data = request.json
    
    prop = Propuesta(
        nombre_cliente=data.get('nombre'),
        paneles=int(data.get('paneles')),
        precio=float(data.get('precio')),
        inversor_marca=data.get('inversor_marca'),
        inversor_modelo=data.get('inversor_modelo'),
        inversor_kw=float(data.get('inversor_kw')),
        inversor_fase=data.get('inversor_fase')
    )
    
    db.session.add(prop)
    db.session.commit()
    
    return jsonify({
        'id': prop.id,
        'link': f"{request.host_url}propuesta/{prop.id}",
        'link_admin': f"{request.host_url}admin/{prop.id}"
    })

@app.route('/propuesta/<prop_id>')
def ver_propuesta(prop_id):
    prop = Propuesta.query.get_or_404(prop_id)
    
    if not prop.fecha_primer_acceso:
        prop.fecha_primer_acceso = datetime.utcnow()
        prop.estado = 'visto'
        db.session.commit()
    
    paneles = prop.paneles
    gen_mes = paneles * 84
    gen_anual = gen_mes * 12
    cap_kw = round(paneles * 0.7, 1)
    
    datos = calcular(prop.precio, paneles, gen_mes)
    aÃ±os_list = list(range(2025, 2045))
    
    return render_template('propuesta.html', 
        prop=prop,
        paneles=paneles,
        gen_mes=gen_mes,
        gen_anual=gen_anual,
        cap_kw=cap_kw,
        datos=datos,
        aÃ±os=aÃ±os_list,
        fmt=fmt
    )

@app.route('/api/evento/<prop_id>', methods=['POST'])
def registrar_evento(prop_id):
    data = request.json
    
    evento = Evento(
        propuesta_id=prop_id,
        tipo=data.get('tipo'),
        seccion=data.get('seccion'),
        valor=data.get('valor')
    )
    
    db.session.add(evento)
    db.session.commit()
    
    return jsonify({'ok': True})

@app.route('/api/visualizacion/<prop_id>', methods=['POST'])
def registrar_visualizacion(prop_id):
    data = request.json
    
    vis = Visualizacion(
        propuesta_id=prop_id,
        ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        duracion_segundos=data.get('duracion', 0)
    )
    
    db.session.add(vis)
    db.session.commit()
    
    return jsonify({'ok': True})

@app.route('/admin')
def admin():
    propuestas = Propuesta.query.order_by(Propuesta.fecha_creacion.desc()).all()
    
    resumen = {
        'total': len(propuestas),
        'vistas': len([p for p in propuestas if p.estado == 'visto']),
        'valor_total': sum([p.precio for p in propuestas]),
        'paneles_totales': sum([p.paneles for p in propuestas])
    }
    
    return render_template('dashboard.html', propuestas=propuestas, resumen=resumen)

@app.route('/admin/<prop_id>')
def admin_detalle(prop_id):
    prop = Propuesta.query.get_or_404(prop_id)
    
    visualizaciones = Visualizacion.query.filter_by(propuesta_id=prop_id).all()
    eventos = Evento.query.filter_by(propuesta_id=prop_id).all()
    
    duracion_total = sum([v.duracion_segundos for v in visualizaciones])
    
    return render_template('detalle_propuesta.html',
        prop=prop,
        visualizaciones=visualizaciones,
        eventos=eventos,
        duracion_total=duracion_total
    )
>>>>>>> 425076e80815fa991fb7133125feef70445c26c9

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
<<<<<<< HEAD
    app.run(debug=False, host='0.0.0.0', port=5000)
=======
    with app.app_context():
        db.create_all()
    app.run(debug=False)
>>>>>>> 425076e80815fa991fb7133125feef70445c26c9
