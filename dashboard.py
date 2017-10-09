import requests
import json

URL_DASH='http://elastic:changeme@localhost:9200/dashboards/users/_search'


REQUEST = '''
{
  "query": {
    "term" : { "email": "%s"} 
  }
}
'''

def get_dashboards(email):

    if email:
       user = email.split('@')[0]
       request = json.loads(REQUEST % user)
       response = requests.post(URL_DASH, json=request)
    if (response.status_code == 200):
        if len(response.json()['hits']['hits']) > 0:
            dashboards = response.json()['hits']['hits'][0]['_source']['dashboards']
            return dashboards
        else:
            raise Exception('Sem dashboards')
    else:
        raise Exception('Erro ao recuperar dados')