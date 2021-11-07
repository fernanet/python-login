from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import MySQLdb.cursors, re, uuid, hashlib, datetime, os

app = Flask(__name__)

# Altere para sua chave secreta (pode ser qualquer coisa, é para proteção extra)
app.secret_key = 'swordfish'

# Configurações do app
app.config['threaded'] = True

# Insira seus detalhes de conexão de banco de dados abaixo
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'fernando'
app.config['MYSQL_PASSWORD'] = 'r!p2Pjedka'
app.config['MYSQL_DB'] = 'ciscorp_bd'

# Insira os detalhes do seu servidor de e-mail abaixo
app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ciscorp.tech@gmail.com'
app.config['MAIL_PASSWORD'] = 'r!p2Pjedka'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Digite seu nome de domínio abaixo
app.config['DOMAIN'] = 'http://ciscorp.com.br'

# Inicializa o MySQL
mysql = MySQL(app)

# Inicializa o E-mail
mail = Mail(app)

# Habilita ativação de conta
account_activation_required = False

# Habilita proteção CSRF?
csrf_protection = False

# http://localhost:5000/login/ - esta será a página de login, precisamos usar solicitações GET e POST
@app.route('/login/', methods=['GET', 'POST'])
def login():
  # Redireciona o usuário para a página inicial se estiver logado
  if loggedin():
        return redirect(url_for('inicio'))
    # Mensagem de saída se algo der errado...
    msg = ''
    # Verifica se existem solicitações POST de "nome de usuário" e "senha" (formulário enviado pelo usuário)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'token' in request.form:
        # Cria variáveis para fácil acesso
        username = request.form['username']
        password = request.form['password']
        token = request.form['token']
        # Recupera a senha com hash
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest();
        # Verifica se a conta existe usando MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE usuario = %s AND senha = %s', (username, password,))
        # Busca um registro e retorna o resultado
        account = cursor.fetchone()
        # Se a conta existe na tabela de contas em nosso banco de dados
        if account:
            if account_activation_required and account['cod_ativ'] != 'ativado' and account['cod_ativ'] != '':
                return 'Por favor, ative sua conta para fazer o login!'
            if csrf_protection and str(token) != str(session['token']):
                return 'Token inválido!'
            # Cria os dados da sessão, podemos acessar esses dados em outras rotas
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['usuario']
            session['role'] = account['funcao']
            if 'rememberme' in request.form:
				# Cria hash para armazenar como cookie
                hash = account['username'] + request.form['password'] + app.secret_key
                hash = hashlib.sha1(hash.encode())
                hash = hash.hexdigest();
				# o cookie expira em 90 dias
                expire_date = datetime.datetime.now() + datetime.timedelta(days=90)
                resp = make_response('Sucesso', 200)
                resp.set_cookie('rememberme', hash, expires=expire_date)
				# Atualiza o lembrete na tabela de contas para o hash do cookie
                cursor.execute('UPDATE contas SET lembranca = %s WHERE id = %s', (hash, account['id'],))
                mysql.connection.commit()
                return resp
            return 'Sucesso'
        else:
            # A conta não existe ou nome de usuário / senha incorretos
            return 'Usuário e/ou senha incorretos!'
    # Gera token aleatório que evitará ataques CSRF
    token = uuid.uuid4()
    session['token'] = token
    # Mostra o formulário de login com mensagem (se houver)
    return render_template('index.html', msg=msg, token=token)

# http://localhost:5000/cadastro - esta será a página de cadastro, precisamos usar as solicitações GET e POST
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Redireciona o usuário para a página inicial se estiver logado
	if loggedin():
		return redirect(url_for('inicio'))
    # Mensagem de saída se algo der errado...
    msg = ''
    # Verifica se existem solicitações POST de "nome de usuário", "senha" e "email" (formulário enviado pelo usuário)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'cpassword' in request.form and 'email' in request.form:
        # Cria variáveis para fácil acesso
        username = request.form['username']
        password = request.form['password']
        cpassword = request.form['cpassword']
        email = request.form['email']
        # Senha com hash
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        hashed_password = hash.hexdigest();

        # Verifica se a conta existe usando MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE usuario = %s', (username,))
        account = cursor.fetchone()
        # Se a conta existir, mostra erros e verificações de validação
        if account:
            msg = 'Essa conta já existe!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Endereço de e-mail inválido!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'O nome de usuário deve conter apenas caracteres e números!'
        elif not username or not password or not cpassword or not email:
            msg = 'Por favor, preencha o formulário!'
        elif account_activation_required:
            # Ativação de conta habilitada
            # Gera uma identificação única aleatória para o código de ativação
            activation_code = uuid.uuid4()
            cursor.execute('INSERT INTO contas VALUES (NULL, %s, %s, %s, %s)', (username, password, email, activation_code,))
            mysql.connection.commit()
            # Altere seu_email@gmail.com
            email_info = Message('Ativação de conta necessária', sender = 'ciscorp@live.com', recipients = [email])
            # mude seudominio.com para o seu site, para testar localmente você pode ir para: http://localhost:5000/login/ativar/<email>/<code>
            activate_link = 'http://localhost:5000/login/ativar/' + str(email) + '/' + str(activation_code)
            # mude o corpo do email abaixo
            email_info.body = '<p>Por favor, clique no link a seguir para ativar sua conta: <a href="' + str(activate_link) + '">' + str(activate_link) + '</a></p>'
            mail.send(email_info)
            msg = 'Por favor, confira seu email para ativar sua conta!'
        else:
            # A conta não existe e os dados do formulário são válidos, agora insira uma nova conta na tabela de contas
            cursor.execute('INSERT INTO contas VALUES (NULL, %s, %s, %s, "")', (username, password, email,))
            mysql.connection.commit()
            msg = 'Cadastro realizado com sucesso!'
    elif request.method == 'POST':
        # Formulário está vazio... (no POST data)
        msg = 'Por favor, preencha o formulário!'
    # Mostra formulário de cadastro com mensagem (se houver)
    return render_template('cadastro.html', msg=msg)

# http://localhost:5000/login/ativar/<email>/<code> - esta página ativará uma conta de usuário se o código de ativação e o e-mail corretos forem fornecidos
@app.route('/login/ativar/<string:email>/<string:code>', methods=['GET'])
def activate(email, code):
    # Verifica se o e-mail e código fornecidos existem na tabela de contas
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM contas WHERE email = %s AND activation_code = %s', (email, code,))
    account = cursor.fetchone()
    if account:
        # se a conta existe, atualiza o código de ativação para "ativado"
        cursor.execute('UPDATE contas SET activation_code = "ativado" WHERE email = %s AND activation_code = %s', (email, code,))
        mysql.connection.commit()
        # imprime mensagem, ou você pode redirecionar para a página de login...
        return 'Conta Ativada!'
    return 'A conta não existe com esse e-mail ou código de ativação incorreto!'

# http://localhost:5000/inicio - esta será a página inicial, acessível apenas para usuários logados
@app.route('/inicio')
def inicio():
    # Verifica se o usuário está logado
    if 'loggedin' in session:
        # Usuário está logado, exibe a página inicial
        return render_template('inicio.html', username=session['username'])
    # Usuário não está logado, redirecionar para a página de login
    return redirect(url_for('login'))

# http://localhost:5000/perfil - esta será a página de perfil, acessível apenas para usuários logados
@app.route('/perfil')
def perfil():
    # Verifica se o usuário está logado
    if 'loggedin' in session:
        # Precisamos de todas as informações da conta do usuário para que possamos exibí-las na página de perfil
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Mostra a página do perfil com informações da conta
        return render_template('perfil.html', account=account)
    # Usuário não está logado no redirecionamento para a página de login
    return redirect(url_for('login'))

# http://localhost:5000/logout - esta será a página de logout
@app.route('/logout')
def logout():
   # Remove os dados da sessão, isso desconectará o usuário
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('usuario', None)

   # Redireciona para a página de login
   return redirect(url_for('login'))

   if __name__ == '__main__':
    app.run()