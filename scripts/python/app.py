# -*- coding: utf-8 -*-
import datetime
import flask
from flask import Flask, Response, render_template, request, flash, redirect, url_for, make_response, jsonify
import json
import logging
import os
import re
import string
import sys
import yaml

from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_pyoidc.user_session import UserSession

app = Flask(__name__)
app.config.update({
    'OIDC_REDIRECT_URI' : os.environ.get('APP_DOMAIN', 'http://localhost') + '/test',
    'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=7).total_seconds(),
                   'DEBUG': True})

@app.route("/hello")
def hello_world():
    return "Hello, world!"



@app.route('/test', methods=['POST'])
def do_tests():
    identifier = request.json.get('identifier')
#    logging.debug(f'test {identifier}')
    #TODO: DONE 1. check that identifier exists in yml
    if not identifier in m_test_ids:
        return f'{identifier} not found!'
    else:
        return f'trying {identifier} ...'
    #TODO: 2. if 1  = True: run the test
    #TODO: 3. return json result
    return 'Done'
#    return make_response(render_template('succes.html',result=app),200)



def stderr(text,nl='\n'):
    sys.stderr.write(f'{text}{nl}')


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

metric_ids = []
m_test_ids = []
with open('data/clarin_fip_metrics_v0.3.yaml', 'r') as f:
    data = yaml.load(f, Loader=yaml.SafeLoader)
    print(data.__class__)
    metrics = data['metrics'] #['metric_tests']
    for i in range(0,len(metrics)):
        metric_ids.append(metrics[i]['metric_identifier'])
        test_list = metrics[i]['metric_tests']
        for j in range(0,len(test_list)):
                m_test_ids.append(test_list[j]['metric_test_identifier'])

    print(metrics.__class__)
    print(len(metrics))
    print(len(metrics[0]['metric_tests']))
    print(metrics[0]['metric_tests'][0]['metric_test_identifier'])
print(metric_ids)
print(m_test_ids)
#    tests = data['metrics']['metric_tests'] 


if __name__ == "__main__":
    app.run()


