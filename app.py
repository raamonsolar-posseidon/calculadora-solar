from flask import Flask

app = Flask(__name__)

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
            <input type="number" placeholder="Número de Paneles" required>
            <button type="submit">Generar Propuesta</button>
        </form>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)