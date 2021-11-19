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
app.config['MYSQL_DB'] = 'ciscorp_db'

# Insira os detalhes do seu servidor de e-mail abaixo
app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ciscorp.tech@gmail.com'
app.config['MAIL_PASSWORD'] = 'r!p2Pjedka'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Digite seu nome de domínio abaixo
app.config['DOMAIN'] = 'localhost:5000'

# Inicializa o MySQL
mysql = MySQL(app)

# Inicializa o E-mail
mail = Mail(app)

# Habilita ativação de conta
account_activation_required = True

# Habilita proteção CSRF?
csrf_protection = True

# http://localhost:5000/entrar/ - esta será a página de login, precisamos usar solicitações GET e POST
@app.route('/entrar', methods=['GET', 'POST'])
def entrar():
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
        hash = account['usuario'] + request.form['password'] + app.secret_key
        hash = hashlib.sha1(hash.encode())
        hash = hash.hexdigest();
		# o cookie expira em 90 dias
        expire_date = datetime.datetime.now() + datetime.timedelta(days=90)
        resp = make_response('Sucesso', 200)
        resp.set_cookie('rememberme', hash, expires=expire_date)
		# Atualiza o lembrete na tabela de contas para o hash do cookie
        cursor.execute('UPDATE contas SET rememberme = %s WHERE id = %s', (hash, account['id'],))
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
      return 'Essa conta já existe!'
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
      return 'Endereço de e-mail inválido!'
    elif not re.match(r'[A-Za-z0-9]+', username):
      return 'O nome de usuário deve conter apenas caracteres e números!'
    elif not username or not password or not cpassword or not email:
      return 'Por favor, preencha o formulário!'
    elif password != cpassword:
      return 'As senhas não conferem!'
    elif len(username) < 5 or len(username) > 20:
      return 'O nome de usuário deve ter entre 5 e 20 caracteres!'
    elif len(password) < 5 or len(password) > 20:
      return 'A senha deve ter entre 5 e 20 caracteres!'
    elif account_activation_required:
      # Ativação de conta habilitada
      # Gera uma id única aleatória para o código de ativação
      activation_code = uuid.uuid4()
      cursor.execute('INSERT INTO contas (usuario, senha, email, cod_ativ) VALUES (%s, %s, %s, %s)', (username, hashed_password, email, activation_code,))
      mysql.connection.commit()
      # Cria nova mensagem
      email_info = Message('Ativação de conta necessária', sender = app.config['MAIL_USERNAME'], recipients = [email])
      # Ativar URL do link
      activate_link = app.config['DOMAIN'] + url_for('ativar', email=email, code=str(activation_code))
      # Define e processa o modelo de e-mail de ativação
      email_info.body = render_template('email.html', link=activate_link)
      email_info.html = render_template('email.html', link=activate_link)
      # envia e-mail de ativação para o usuário
      mail.send(email_info)
      return 'Por favor, confira seu email para ativar sua conta!'
    else:
      # A conta não existe e os dados do formulário são válidos, agora insira uma nova conta na tabela de contas
      cursor.execute('INSERT INTO contas (usuario, senha, email, cod_ativ) VALUES (%s, %s, %s, "ativado")', (username, hashed_password, email,))
      mysql.connection.commit()
      return 'Cadastro realizado com sucesso!'
  elif request.method == 'POST':
    # Formulário está vazio... (no POST data)
    return 'Por favor, preencha o formulário!'
  # Mostra formulário de cadastro com mensagem (se houver)
  return render_template('cadastro.html', msg=msg)

# http://localhost:5000/ativar/<email>/<code> - esta página ativará uma conta de usuário se o código de ativação e o e-mail corretos forem fornecidos
@app.route('/ativar/<string:email>/<string:code>', methods=['GET'])
def ativar(email, code):
    msg = 'A conta não existe com esse e-mail ou o código de ativação está incorreto!'
    # Verifica se o e-mail e código fornecidos existem na tabela de contas
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM contas WHERE email = %s AND cod_ativ = %s', (email, code,))
    account = cursor.fetchone()
    if account:
      # se a conta existe, atualiza o código de ativação para "ativado"
      cursor.execute('UPDATE contas SET cod_ativ = "ativado" WHERE email = %s AND cod_ativ = %s', (email, code,))
      mysql.connection.commit()
      # loga automaticamente o usuário e redireciona para a página inicial
      session['loggedin'] = True
      session['id'] = account['id']
      session['username'] = account['usuario']
      session['role'] = account['funcao']
      return redirect(url_for('inicio'))
    return render_template('ativacao.html', msg=msg)

# http://localhost:5000/inicio - esta será a página inicial, acessível apenas para usuários logados
@app.route('/inicio')
def inicio():
    # Verifica se o usuário está logado
    if 'loggedin' in session:
        # Usuário está logado, exibe a página inicial
        return render_template('inicio.html', username=session['username'], role=session['role'])
    # Usuário não está logado, redireciona para a página de login
    return redirect(url_for('entrar'))

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
        return render_template('perfil.html', account=account, role=session['role'])
    # Usuário não está logado, no redireciona para a página de login
    return redirect(url_for('entrar'))

# http://localhost:5000/perfil/editar - o usuário pode editar seus detalhes existentes
@app.route('/perfil/editar', methods=['GET', 'POST'])
def editar_perfil():
	# Verifica se o usuário está logado
	if loggedin():
		# Precisamos de todas as informações da conta do usuário para que possamos exibí-las na página de perfil
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		# Mensagem de saída
		msg = ''
		# Verifica se existem solicitações POST de "nome de usuário", "senha" e "email" (formulário enviado pelo usuário)
		if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
			# Cria variáveis para fácil acesso
			username = request.form['username']
			password = request.form['password']
			email = request.form['email']
			# Recupera conta pelo nome de usuário
			cursor.execute('SELECT * FROM contas WHERE usuario = %s', (username,))
			account = cursor.fetchone()
			# verificação de validação
			if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
				msg = 'Endereço de e-mail inválido!'
			elif not re.match(r'[A-Za-z0-9]+', username):
				msg = 'O nome de usuário deve conter apenas caracteres e números!'
			elif not username or not email:
				msg = 'Por favor, preencha o formulário!'
			elif session['username'] != username and account:
				msg = 'Nome de usuário já existe!'
			elif len(username) < 5 or len(username) > 20:
				return 'O nome de usuário deve ter entre 5 e 20 caracteres!'
			elif len(password) < 5 or len(password) > 20:
				return 'A senha deve ter entre 5 e 20 caracteres!'
			else:
				cursor.execute('SELECT * FROM contas WHERE id = %s', (session['id'],))
				account = cursor.fetchone()
				current_password = account['senha']
				if password:
					# Hash a senha
					hash = password + app.secret_key
					hash = hashlib.sha1(hash.encode())
					current_password = hash.hexdigest();
				# atualiza a conta com os novos detalhes
				cursor.execute('UPDATE contas SET usuario = %s, senha = %s, email = %s WHERE id = %s', (username, current_password, email, session['id'],))
				mysql.connection.commit()
				msg = 'Atualizado!'
		cursor.execute('SELECT * FROM contas WHERE id = %s', (session['id'],))
		account = cursor.fetchone()
		# Mostra a página do perfil com informações da conta
		return render_template('editar.html', account=account, role=session['role'], msg=msg)
	return redirect(url_for('entrar'))

# http://localhost:5000/recuperar - o usuário pode usar esta página se tiver esquecido sua senha
@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
	msg = ''
	if request.method == 'POST' and 'email' in request.form:
		email = request.form['email']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM contas WHERE email = %s', (email,))
		account = cursor.fetchone()
		if account:
			# Gera ID único
			reset_code = uuid.uuid4()
			# Atualiza a coluna de redefinição na tabela de contas para refletir o ID gerado
			cursor.execute('UPDATE contas SET reset = %s WHERE email = %s', (reset_code, email,))
			mysql.connection.commit()
			# Altera seu_email@gmail.com
			email_info = Message('Redefinição de senha', sender = app.config['MAIL_USERNAME'], recipients = [email])
			# Gera link de redefinição de senha
			reset_link = app.config['DOMAIN'] + url_for('redefinir', email = email, code = str(reset_code))
			# muda o corpo do email abaixo
			email_info.body = 'Por favor, clique no link a seguir para redefinir sua senha: ' + str(reset_link)
			email_info.html = '<p>Por favor, clique no link a seguir para redefinir sua senha: <a href="' + str(reset_link) + '">' + str(reset_link) + '</a></p>'
			mail.send(email_info)
			msg = 'O link de redefinição de senha foi enviado para seu e-mail!'
		else:
			msg = 'Não existe uma conta com esse e-mail!'
	return render_template('recuperar.html', msg=msg)

# http://localhost:5000/redefinir/EMAIL/CODE - prossegue para redefinir a senha do usuário
@app.route('/redefinir/<string:email>/<string:code>', methods=['GET', 'POST'])
def redefinir(email, code):
	msg = ''
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	# Recupera a conta com o e-mail e o código de redefinição fornecido na solicitação GET
	cursor.execute('SELECT * FROM contas WHERE email = %s AND reset = %s', (email, code,))
	account = cursor.fetchone()
	# Se a conta existe
	if account:
		# Verifica se os novos campos de senha foram enviados
		if request.method == 'POST' and 'npassword' in request.form and 'cpassword' in request.form:
			npassword = request.form['npassword']
			cpassword = request.form['cpassword']
			# Os campos de senha devem corresponder
			if npassword == cpassword and npassword != "":
				# Hash de nova senha
				hash = npassword + app.secret_key
				hash = hashlib.sha1(hash.encode())
				npassword = hash.hexdigest();
				# Atualiza a senha do usuário
				cursor.execute('UPDATE contas SET senha = %s, reset = "" WHERE email = %s', (npassword, email,))
				mysql.connection.commit()
				msg = 'Sua senha foi redefinida, agora você pode <a href="' + url_for('entrar') + '">efetuar login</a>!'
			else:
				msg = 'As senhas devem corresponder e não devem estar em branco!'
		return render_template('redefinir.html', msg=msg, email=email, code=code)
	return 'E-mail e/ou código inválido!'

# http://localhost:5000/logout - esta será a página de logout
@app.route('/logout')
def logout():
   # Remove os dados da sessão, isso desconectará o usuário
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('role', None)

   # Remove os dados do cookie "lembre-se de mim"
   resp = make_response(redirect(url_for('entrar')))
   resp.set_cookie('rememberme', expires=0)
   return resp

# Verifica se a função está logada, atualiza a sessão se o cookie para "lembrar de mim" existir
def loggedin():
	if 'loggedin' in session:
		return True
	elif 'rememberme' in request.cookies:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		# verifique se está lembrado, o cookie deve corresponder ao campo "lembrar-me"
		cursor.execute('SELECT * FROM contas WHERE rememberme = %s', (request.cookies['rememberme'],))
		account = cursor.fetchone()
		if account:
			# atualiza variáveis de sessão
			session['loggedin'] = True
			session['id'] = account['id']
			session['username'] = account['usuario']
			session['role'] = account['funcao']
			return True
	# a conta não está logada, então retorna falso
	return False

# Importa o arquivo admin
import admin

if __name__ == '__main__':
    app.run()