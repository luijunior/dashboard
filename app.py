from flask import Flask, render_template,request , redirect, make_response, session as login_session
import requests
import random
import string
from simplekv.memory import DictStore
from dashboard import get_dashboards
import json
from googleapiclient.discovery import build
from flask_kvsession import KVSessionExtension
import google_connect

app = Flask(__name__)
store = DictStore()
KVSessionExtension(store, app)
URL_DASH='http://elastic:changeme@localhost:9200/dashboards/marketing/1/_source'
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
SERVICE = build('plus', 'v1')


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/logout')
def logout():
    if 'username' not in login_session:
        return redirect('/login')
    del login_session['username']
    return redirect('/login')


@app.route('/', methods=['GET'])
def home():
    if 'username' not in login_session:
        return redirect('/login')
    try:
        dashboards = get_dashboards(login_session['email'])
        login_session['dashboards'] = dashboards
        return render_template('index.html', dashboards=dashboards, sucesso=True)
    except Exception as err:
        return render_template('index.html', msg=err, sucesso=False)


@app.route('/<dash_name>', methods=['GET'])
def render_dash(dash_name):

    if 'username' not in login_session:
        return redirect('/login')
    if 'dashboards' not in login_session:
        return render_template('index.html', msg='Sem permissao para acessar o dashboard %s' % dash_name, sucesso=False)
    d = dict((i['name'], i['frame']) for i in login_session['dashboards'])
    if dash_name not in d:
        return render_template('index.html', msg='Sem permissao para acessar o dashboard %s' % dash_name, sucesso=False)
    return render_template('dashboard.html', dashboard=d[dash_name], sucesso=True)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    sucesso_code, retorno_code = google_connect.troca_code_por_credenciais(code)
    if not sucesso_code:
        return retorno_code
    credentials = retorno_code
    access_token = credentials.access_token
    sucesso_token, retorno_token = google_connect.verifica_se_access_e_valido(access_token)
    if not sucesso_token:
        return retorno_token
    # Verifica se o token enviado é do usuario
    sucesso_gplus_id, response_gplus_id = google_connect.verifica_se_token_e_do_user(credentials, retorno_token, CLIENT_ID)
    if not sucesso_gplus_id:
        return response_gplus_id
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    # Usuario connectado
    if stored_access_token is not None and response_gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Guarda o access_token
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = response_gplus_id

    # Busca dados do usuario
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['user_id'] = data['id']
    return 'home'


if __name__ == '__main__':
    app.debug = True
    app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                             for x in range(32))
    app.run(host='0.0.0.0', port=8080)
