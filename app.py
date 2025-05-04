from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dados.db'
db = SQLAlchemy(app)

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emitente = db.Column(db.String(40), nullable=False)
    classificação = db.Column(db.String(15), nullable=False)
    empresa = db.Column(db.String(15), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    local = db.Column(db.String(20), nullable=False)
    observação = db.Column(db.String(150), nullable=False)
    ação = db.Column(db.String(150), nullable=False)  # Ação imediata
    class_sst = db.Column(db.String(300), nullable=True)              # Apenas um? sst/ambiental
    class_ambiental = db.Column(db.String(300), nullable=True)         # Apenas um? sst/ambiental
    causa = db.Column(db.String(300), nullable=True)                   # Deve ser múltipla escolha ?
    parecer = db.Column(db.String(100), nullable=True)               #    Discutir necessidade e utilidade <<<< ("Estabelecer ações posteriores")
    num_ordem_man = db.Column(db.String(20), nullable=True)            # Número da Ordem de Manutenção
    obs_sprocedencia = db.Column(db.String(20), nullable=True)         # Observação sem procedência
    obs_justificativa = db.Column(db.String(20), nullable=True)         # Justificativa 
    multipla_condição = db.Column(db.String(60), nullable=True)       # Multipla condição insegura
    multipla_comportamento = db.Column(db.String(60), nullable=True)       # Multipla Comportamento Inseguro
    multipla_ambiental = db.Column(db.String(60), nullable=True)       # Multipla Ocorrência Ambiental
    verificação = db.Column(db.String(20), nullable=True)

with app.app_context():
    db.create_all()

def init_auth_db():
    with sqlite3.connect("usuarios.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )''')

        c.execute("INSERT OR IGNORE INTO usuarios (id, username, password) VALUES (1, 'teste', '1234')")
        conn.commit()

init_auth_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["username"]
        senha = request.form["password"]
        with sqlite3.connect("usuarios.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (usuario, senha))
            user = c.fetchone()
            if user:
                session["logado"] = True
                return redirect(url_for("ssma"))
        return "Login inválido!"
    return render_template("login.html")

@app.route("/ssma", methods=["GET", "POST"])            # Pagina exclusiva do SSMA 
def ssma():
    if not session.get("logado"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        ids = request.form.getlist("id_list")

        for entrada_id in ids:
            entrada = Entrada.query.get(entrada_id)
            if entrada:
                entrada.class_sst = request.form.get(f"class_sst_{entrada_id}", "")
                entrada.class_ambiental = request.form.get(f"class_ambiental_{entrada_id}", "")
                entrada.causa = ', '.join(request.form.getlist(f"causa_{entrada_id}"))
                entrada.parecer = request.form.get(f"parecer_{entrada_id}", "")
                entrada.num_ordem_man = request.form.get(f"num_ordem_man_{entrada_id}", "")
                entrada.obs_sprocedencia = request.form.get(f"obs_sprocedencia_{entrada_id}", "")
                entrada.obs_justificativa = request.form.get(f"obs_justificativa_{entrada_id}", "")
                entrada.multipla_condição = ', '.join(request.form.getlist(f"multipla_condição_{entrada_id}"))
                entrada.multipla_comportamento = ', '.join(request.form.getlist(f"multipla_comportamento_{entrada_id}"))
                entrada.multipla_ambiental = ', '.join(request.form.getlist(f"multipla_ambiental_{entrada_id}"))
                entrada.verificação = request.form.get(f"verificação_{entrada_id}", "")
        
        db.session.commit()
        return redirect(url_for("ssma"))  # recarrega após salvar

    entradas = Entrada.query.all()
    return render_template("ssma.html", entradas=entradas)


# Formulário de abertura
@app.route("/abertura", methods=["GET", "POST"])
def abertura():
    if request.method == 'POST':
        emitente = request.form['emitente']
        classificação = request.form['classificação']
        empresa = request.form['empresa']
        data = datetime.strptime(request.form['data'], "%Y-%m-%d").date()
        hora = datetime.strptime(request.form['hora'], "%H:%M").time()
        local = request.form['local']
        observação = request.form['observação']
        ação = request.form['ação']
        class_sst = request.form.get('class_sst')
        class_ambiental = request.form.get('class_ambiental')
        causa = ','.join(request.form.getlist('causa'))
        parecer = request.form.get('parecer')
        num_ordem_man = request.form.get('num_ordem_man')
        obs_sprocedencia = request.form.get('obs_sprocedencia')
        obs_justificativa = request.form.get('obs_justificativa')
        multipla_condição = ','.join(request.form.getlist('multipla'))
        multipla_comportamento = ','.join(request.form.getlist('multipla'))
        multipla_ambiental = ','.join(request.form.getlist('multipla'))
        verificação = request.form.get('verificação')

        nova_entrada = Entrada(
            emitente=emitente,
            classificação=classificação,
            empresa=empresa,
            data=data,
            hora=hora,
            local=local,
            observação=observação,
            ação=ação,
            class_sst=class_sst,
            class_ambiental=class_ambiental,
            causa=causa,
            parecer=parecer,
            num_ordem_man=num_ordem_man,
            obs_sprocedencia=obs_sprocedencia,
            obs_justificativa=obs_justificativa,
            multipla_condição=multipla_condição,
            multipla_comportamento=multipla_comportamento,
            multipla_ambiental=multipla_ambiental,
            verificação=verificação,
        )
        db.session.add(nova_entrada)
        db.session.commit()


    entradas = Entrada.query.all()
    return render_template('abertura.html', entradas=entradas)

   # Graficos, teste
@app.route('/graficos')
def graficos():
    entradas = Entrada.query.all()

    # Contagem de (classificações)
    contagem = {}
    for entrada in entradas:
        key = entrada.classificação
        contagem[key] = contagem.get(key, 0) + 1

    # Geração do Gráfico
    fig, ax = plt.subplots()
    categorias = list(contagem.keys())
    valores = list(contagem.values())

    ax.bar(categorias, valores, color='skyblue')
    ax.set_title('Ocorrências por Classificação')
    ax.set_ylabel('Quantidade')
    ax.set_xlabel('Classificação')
    plt.xticks(rotation=0)

    # Salva para o buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    imagem_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render_template('graficos.html', imagem=imagem_base64)

if __name__ == "__main__":
    app.run(debug=True)