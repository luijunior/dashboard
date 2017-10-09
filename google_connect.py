from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import json
import requests


def troca_code_por_credenciais(code):
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        return True, credentials
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return False, response


def verifica_se_access_e_valido(access_token):
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    result = requests.get(url).json()
    # Se tiver erro no access_token retornar erro
    if 'error' in result:
        response = make_response(json.dumps(result['error']), 500)
        response.headers['Content-Type'] = 'application/json'
        return False, response
    else:
        return True, result


def verifica_se_token_e_do_user(credentials, result, client_id):
    # Verifica se o token enviado é do usuario
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return False, response
    # Verifica se o access_token é valido para o app
    if result['issued_to'] != client_id:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print
        "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return False, response
    return True, gplus_id