from main import app, mysql, MySQLdb, render_template, request, redirect, url_for, session, loggedin, hashlib, os

# http://localhost:5000/admin/ - página inicial do administrador, visualiza todas as contas
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Verifica se o administrador está logado
    if not admin_loggedin():
        return redirect(url_for('entrar'))
    msg = ''
    # Recupera todas as contas do banco de dados
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM contas')
    accounts = cursor.fetchall()
    return render_template('admin/index.html', accounts=accounts)

# http://localhost:5000/admin/conta - cria ou edita uma conta
@app.route('/admin/conta/<int:id>', methods=['GET', 'POST'])
@app.route('/admin/conta', methods=['GET', 'POST'], defaults={'id': None})
def conta_admin(id):
    # Verifica se o administrador está logado
    if not admin_loggedin():
        return redirect(url_for('entrar'))
    page = 'Criar'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Valores de conta de entrada padrão
    account = {
        'usuario': '',
        'senha': '',
        'email': '',
        'cod_ativ': '',
        'rememberme': '',
        'funcao': 'Usuário'
    }
    roles = ['Usuário', 'Admin'];
    # requisição GET ID existe, editar conta
    if id:
        # Edita uma conta existente
        page = 'Editar'
        # Recupera conta por ID com o ID de solicitação GET
        cursor.execute('SELECT * FROM contas WHERE id = %s', (id,))
        account = cursor.fetchone()
        if request.method == 'POST' and 'submit' in request.form:
            # atualiza conta
            password = account['senha']
            if account['senha'] != request.form['password']:
                 hash = request.form['password'] + app.secret_key
                 hash = hashlib.sha1(hash.encode())
                 password = hash.hexdigest();
            cursor.execute('UPDATE contas SET usuario = %s, senha = %s, email = %s, cod_ativ = %s, rememberme = %s, funcao = %s WHERE id = %s', (request.form['username'],password,request.form['email'],request.form['activation_code'],request.form['rememberme'],request.form['role'],id,))
            mysql.connection.commit()
            return redirect(url_for('admin'))
        if request.method == 'POST' and 'delete' in request.form:
            # exclui conta
            cursor.execute('DELETE FROM contas WHERE id = %s', (id,))
            mysql.connection.commit()
            return redirect(url_for('admin'))
    if request.method == 'POST' and request.form['submit']:
        # Cria nova conta
        hash = request.form['password'] + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest();
        cursor.execute('INSERT INTO contas (usuario, senha , email, cod_ativ, rememberme, funcao) VALUES (%s,%s,%s,%s,%s,%s)', (request.form['username'],password,request.form['email'],request.form['activation_code'],request.form['rememberme'],request.form['role'],))
        mysql.connection.commit()
        return redirect(url_for('admin'))
    return render_template('admin/conta.html', account=account, page=page, roles=roles)

# http://localhost:5000/admin/email - página de modelo de e-mail do administrador, edite o modelo existente
@app.route('/admin/email', methods=['GET', 'POST'])
def admin_email():
    # Verifica se o administrador está logado
    if not admin_loggedin():
        return redirect(url_for('entrar'))
    # Obtém o caminho do diretório do modelo
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    # Atualiza o arquivo de modelo ao salvar
    if request.method == 'POST':
        content = request.form['content'].replace('\r', '')
        open(template_dir + '/email.html', mode='w', encoding='utf-8').write(content)
    # Lê o modelo de e-mail de ativação
    content = open(template_dir + '/email.html', mode='r', encoding='utf-8').read()
    return render_template('admin/email.html', content=content)

# Função que verifica se o administrador está logado
def admin_loggedin():
    if loggedin() and session['role'] == 'Admin':
        # admin está logado
        return True
    # admin não está logado retorna falso
    return False