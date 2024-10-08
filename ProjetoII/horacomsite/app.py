from flask import Flask,render_template,request,redirect,url_for,session,flash,jsonify
from flask_login import LoginManager, logout_user
from flask_sqlalchemy import SQLAlchemy  # Biblioteca para bd
import mysql.connector  # Para conectar ao MySQL
from routes.models import User  # Importando o modelo de usuário
from routes.config import db_get_config,somar_horas_certificados,get_nome_usuario_logado
import os  # Para interagir com o sistema operacional
from jinja2 import Environment  # Mecanismo de modelo usado pelo Flask
import zipfile  # Para manipulação de arquivos zip
from flask import flash


app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'CamilaFer123*'  
login_manager = LoginManager(app)
login_manager.login_view = 'acesso'


# Adicione a função basename ao ambiente Jinja2 - Utilizamos para suprimir o nome do tipo e apresentar apenas o nome salvo do arquivo
env = Environment()
env.filters['basename'] = lambda path: os.path.basename(path)
app.jinja_env.filters.update(basename=lambda path: os.path.basename(path))

def basename(path):
    if isinstance(path, bytearray):
        path = path.decode('utf-8')  # Decodificar bytearray para string
    return os.path.basename(path)

# Adicione a função basename ao ambiente Jinja2
app.jinja_env.filters.update(basename=basename)


# Inicialize o objeto SQLAlchemy com a aplicação Flask
db = SQLAlchemy()

def create_app():# Criação de instancia e acesso bd 
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:amarelo123*@localhost/horacom'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


with app.app_context():#Permite o Flask acessar o banco de dados 
    conexao = mysql.connector.connect(**db_get_config())#Cria conexão com BD


# Recupera o usuário do banco de dados com base no email - com flask-login - 1
@login_manager.user_loader
def load_user(user_id):    
    usuario = User.query.filter_by(email=user_id).first()
    return usuario

#Rota da pagina incial - Rota ok - 2
@app.route('/')
def index():
    return render_template('index.html')

#Rota que permite acesso do usuario - ROTA OK - 3 
@app.route('/acesso/<data>', methods=['GET'])
def acesso():
    # Verifica se 'email' está na sessão
    if 'email' in session:
        data = request.args.get('data')
        next_url = request.args.get('next')

        # Redireciona com base em 'data' e 'next_url'
        if data:
            return redirect(url_for('user_academic', email=session['email'], data=data, next=next_url) if next_url else url_for('user_academic', email=session['email'], data=data))
        else:
            return redirect(url_for('user_academic', email=session['email'], next=next_url) if next_url else url_for('user_academic', email=session['email']))

    # Se 'email' não estiver na sessão, renderiza o template de login
    return render_template('login.html')


#Acesso para pagina de login - ROTA OK - 4 
@app.route('/login') 
def login():
    return render_template('login.html')

# Processar login - ROTA OK - 5 com mensagem de erro caso a senha seja digitada incorretamente
@app.route('/processar_login', methods=['POST'])
def processar_login():
    email = request.form.get('email')
    senha = request.form.get('senha')

    if not email or not senha:
        flash('E-mail e senha são obrigatórios.', 'error')
        return redirect(url_for('acesso'))

    app.logger.debug(f"Email: {email}, Senha: {senha}")

    cursor = conexao.cursor()
    try:
        consulta = f"SELECT tipo_usuario, nome FROM usuarios WHERE email = '{email}' AND senha = '{senha}'"
        cursor.execute(consulta)
        resultado = cursor.fetchone()

        if resultado:
            tipo_usuario, nome_usuario = resultado
            app.logger.debug(f"Nome do usuário encontrado no banco de dados: {nome_usuario}")
            session['tipo_usuario'] = tipo_usuario
            session['email'] = email
            session['usuario_nome'] = nome_usuario

            if tipo_usuario == 'academico':
                app.logger.debug("User academic")
                return redirect(url_for('user_academic', data=email))
            elif tipo_usuario == 'coordenador':
                app.logger.debug("User coordenador")
                return redirect(url_for('user_coordenador', data=email))
            else:
                flash('Usuário não reconhecido.', 'error')
                return redirect(url_for('acesso'))

        else:
            # Adicione uma mensagem de erro para senhas incorretas
            flash('E-mail ou senha incorretos. Tente novamente.', 'error')
            return render_template('pagina_erro.html', mensagem_erro='E-mail ou senha incorretos. Tente novamente.')

    except mysql.connector.Error as err:
        app.logger.error(f"Erro na consulta ao banco de dados: {err}")
        flash('Erro ao consultar o banco de dados. Tente novamente mais tarde.', 'error')
        return render_template('pagina_erro.html', mensagem_erro='Erro ao consultar o banco de dados. Tente novamente mais tarde.')

    finally:
        cursor.fetchall()
        cursor.close()

    conexao.close()
    return redirect(url_for('acesso'))


#Rota da Pagina do Academico - ROTA OK - 6 
@app.route('/user_academic/<data>', methods=['GET', 'POST'])#mudar rota com dado do email
def user_academic(data):#variavel data contem email - para vincular o acesso do usuario
    nome_usuario = get_nome_usuario_logado()
    #print("Tipo de usuário:", current_user.tipo_usuario)
    print("Renderizando useracademic.html")
    return render_template('useracademic.html',data=data,nome_usuario=nome_usuario)
    #else:
    #    print("Redirecionando para acesso")
    #    return redirect(url_for('acesso'))

#Rota para pagina do Coordenador - ROTA OK - 7 
@app.route('/user_coordenador')
def user_coordenador():
    print("Renderizando user_coordenador.html")
    return render_template('user_coordenador.html')

#Rota para sair - ROTA OK - 8 
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#Rota do cadastro para inserir no banco de dados as informações do usuario - ROTA OK - 9
@app.route('/cadastro', methods=['POST'])
def processar_cadastro():
    email = request.form['email']
    senha = request.form['senha']
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    tipo_usuario = request.form.get('tipo_usuario', 'academico')  # Padrão para 'academico' se não estiver presente
    
    if conexao:
        try:
            cursor = conexao.cursor()
            consulta = f"INSERT INTO usuarios (nome, cpf, tipo_usuario,email, senha) VALUES ('{nome}', '{cpf}', '{tipo_usuario}','{email}', '{senha}')"
            cursor.execute(consulta)
            conexao.commit()
            
            
        except mysql.connector.Error as err:
            print(f"Erro no processamento do cadastro: {err}")
            conexao.rollback()
        finally:
            cursor.close()
            
    return render_template('login.html')

#Rota para acessar a pagina cadastro - ROTA OK - 10
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

#EM ANDAMENTO - 11 
@app.route('/esqueceusenha', methods=['GET', 'POST'])
def esqueceusenha():
    if request.method == 'POST':
        return render_template('email_enviado.html')

    return render_template('esqueceusenha.html')

#EM ANDAMENTO - 12
@app.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')

        # Lógica para atualizar a senha do usuário no banco de dados
        
        return redirect(url_for('acesso'))

    # Renderizar a página de redefinição de senha
    return render_template('redefinir_senha.html', token=token)

#EM ANDAMENTO - 13
@app.route('/editar_cadastro')
def editar_cadastro():
    return render_template('editarcadastro.html')

#Rota da pagina anexar - ROTA OK - 14 
@app.route('/anexar/<data>')
def anexar(data):
    return render_template('anexar.html',data=data)

#Rota para anexar certificado - ROTA OK - 15
@app.route('/anexar_certificado/<data>',methods=['POST'])
def anexar_certificado(data):
    # print('entrou')
    anexo = request.form['arquivo']
    # print('anexo ok')
    grupo = request.form['grupoPrincipal']
    # print(grupo)
    
    hora = float(request.form['horasDesejadas'])
    
    if (grupo == 'g1'):
        opcao = request.form['subGrupoG1']
        if opcao == "opcao1":
            hora = hora/4
        elif opcao =="opcao5" or opcao == "opcao9" or opcao == "opcao16":
            hora = hora/2
        elif opcao == "opcao3" or opcao == "opcao11":
            hora = 20
        elif opcao == "opcao4":
            hora = 1
        elif opcao == "opcao10" or opcao == "opcao13":
            hora = 40
        elif opcao == "opcao12":
            hora = 10        
        elif opcao == "opcao14":
            hora = 80
        elif opcao == "opcao17":
            hora = 6        
        elif opcao == "opcao18":
            hora = 3
        # print("entrou g1")
    else:
        # print("entrou g2")
        opcao = request.form['subGrupoG2']
        if opcao == "opcao1" or opcao == "opcao2":
            hora = hora/4
        elif opcao == "opcao3":
            hora = 10
        else:
            if hora > 30:
                hora = 30

    if (grupo == 'g1'):
        opcao = request.form['subGrupoG1']
        if opcao == "opcao1" or opcao =="opcao2" or opcao == "opcao8" or opcao == "opcao9" or opcao == "opcao15" or opcao == "opcao16" or opcao == "opcao17" or opcao == "opcao18" or opcao == "opcao19":
            peso = 60
        elif opcao=="opcao3" or opcao == "opcao6" or opcao == "opcao10" or opcao == "opcao11" or opcao == "opcao12" or opcao == "opcao13" or opcao == "opcao14":
            peso = 80
        elif opcao=="opcao4" or opcao=="opcao5":
            peso = 20
        else:
            peso =  40
        # print("entrou g1")
    else:
        # print("entrou g2")
        opcao = request.form['subGrupoG2']
        if opcao == "opcao1" or opcao == "opcao2":
            peso = 120
        else:
            peso = 60 

    email = data
    if conexao:
        try:
            cursor = conexao.cursor()
            consulta = f"select sum(hora) from certificados where email = '{email}' and grupo = '{grupo}' and opcao = '{opcao}';"
            cursor.execute(consulta)
            resultado = cursor.fetchone()
                        
        except mysql.connector.Error as err:
            print(f"Erro na soma dos certificados: {err}")
            conexao.rollback()
    #Peso = Quantidade maxima
    #Resultado = Quantidade já computada
    #Hora = Quantidade informada
    print(resultado[0])
    if resultado[0] == None:
        resultado = 0
    else:
        resultado = float(resultado[0])
    if(hora > peso - resultado):
        hora = peso - resultado
    # print(horas)
    #print(email)

    if conexao:
        try:
            cursor = conexao.cursor()
            consulta = f"INSERT INTO certificados (email, grupo, opcao,hora, anexo) VALUES ('{email}', '{grupo}', '{opcao}','{float(hora)}', '{anexo}')"
            cursor.execute(consulta)
            conexao.commit()
                        
        except mysql.connector.Error as err:
            print(f"Erro no processamento do cadastro: {err}")
            conexao.rollback()

    return redirect(url_for('relatorio', data=email))


#Relatório para user_academico -  ROTA OK - 16 
@app.route('/relatorio/<data>',methods=['POST', 'GET'])
def relatorio(data):
    cursor = conexao.cursor()
    nome_usuario = get_nome_usuario_logado()
    try:
        # print("Entrou na função relatorio_certificados")
        consulta = "SELECT * FROM certificados WHERE email=%s"
        cursor.execute(consulta, (data,))
        resultado = cursor.fetchall()
        # print(resultado)

        # Calcular a soma das hor.as
        email = data  # Use o valor 'data' como o email para a função
        somar_horas = somar_horas_certificados(email)
        # print(somar_horas)

    except mysql.connector.Error as err:
        print(f"Erro na consulta ao banco de dados: {err}")
        return redirect(url_for('acesso'))
    finally:
        cursor.close()

    
    return render_template('relatorio.html', data=resultado, somar_horas=somar_horas,nome_usuario=nome_usuario)

#Rota para retornar os relatórios do BD de todos para o coordenador - ROTA OK - 17
@app.route('/relatoriocoordenador', methods=['GET'])
def relatoriocoordenador():
    cursor = conexao.cursor()
    try:
        # Obter a lista de acadêmicos (usuários de tipo 'academico')
        consulta_academicos = "SELECT email, nome FROM usuarios WHERE tipo_usuario = 'academico'"
        cursor.execute(consulta_academicos)
        academicos = cursor.fetchall()

        # Calcular a soma total de horas para cada acadêmico
        resultado = []
        for academico in academicos:
            email = academico[0]
            nome = academico[1]
            soma_horas = somar_horas_certificados(email)
            resultado.append({'nome_usuario': nome, 'soma_horas': soma_horas})

    except mysql.connector.Error as err:
        print(f"Erro na consulta ao banco de dados: {err}")
        return redirect(url_for('acesso'))
    finally:
        cursor.close()

    return render_template('relatoriocoordenador.html', data=resultado)

#EM ANDAMENTO - 18
#AINDA NÃO ESTA ZIPANDO TENSO
@app.route('/extrairzip', methods=['GET', 'POST'])
def extrairzip():
    if request.method == 'POST':
        # Certifique-se de que o diretório de destino exista
        target_directory = os.path.join(os.path.expanduser('~'), 'Desktop', 'horacom')
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # Diretório de origem (certificados na área de trabalho)
        source_directory = os.path.join(os.path.expanduser('~'), 'Desktop', 'certificados')

        # Nome do arquivo zip
        zip_filename = "certificados.zip"

        # Caminho completo para o arquivo zip
        zip_path = os.path.join(target_directory, zip_filename)

        try:
            # Tentar zipar o conteúdo do diretório
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for foldername, subfolders, filenames in os.walk(source_directory):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        arcname = os.path.relpath(file_path, source_directory)
                        zip_file.write(file_path, arcname)

            # Renderize a página sucesso.html com o caminho do arquivo ZIP
            return render_template('sucesso.html', caminho_zip=zip_path)

        except Exception as e:
            # Tratar caso ocorra algum erro durante o processo
            return render_template('pagina_erro.html', error_message=f"Erro ao zipar pasta de certificados: {e}")

    return render_template('extrairzip.html')


#EM ANDAMENTO - 19
@app.route('/upload')
def upload():
    return render_template('upload.html')

#Rota 20 ROTA Contato ok fiz direto no formulario do html o envio  
@app.route('/contato', methods=['GET', 'POST'])
def contato():
   return render_template('contato.html')

#Rota 21 ok para mensagens de erro
@app.route('/pagina_erro')
def pagina_erro():
    # Obtenha a mensagem de erro da sessão
    erro_senha = session.pop('_flashes', None)
    return render_template('pagina_erro.html',erro_senha=erro_senha)

#Rota 22 ok para grafico
@app.route('/get_grafico/<data>')
def get_grafico(data):
    # Obter o valor da soma de horas diretamente do relatório
    somar_horas_relatorio = somar_horas_certificados(data)

    # Montar os dados do gráfico em formato JSON
    grafico_data = {
        'labels': ['REALIZADAS', 'FALTAM'],
        'sizes': [somar_horas_relatorio, max(0, 240 - somar_horas_relatorio)],  # Assumindo uma meta total de 240 horas
        'colors': ['#005200', '#BA0000']
    }

    return jsonify(grafico_data)



#------------- ROTAS ESTATICAS -----------------# 
@app.route('/sucesso')
def sucesso():
    return render_template('sucesso.html') 

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/storyboard')
def storyboard():
    return render_template('storyboard.html')

@app.route('/idealizadoras')
def idealizadoras():
    return render_template('idealizadoras.html')

@app.route('/persona')
def persona():
    return render_template('persona.html')    

@app.route('/saibamais')
def saibamais():
    return render_template('saibamais.html')

@app.route('/tabela')
def tabela():
    return render_template('tabela.html')



if __name__ == '__main__':
    app.run(debug=True)
