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

from flask_pyoidc import OIDCAuthentication
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



@app.route('/test/<identifier>', methods=['POST'])
def do_tests(identifier):
    #TODO: 1. check that identifier exists in yml
#    logging.debug(f'test {identifier}')
    #TODO: 2. if 1  = True: run the test
    #TODO: 3. return json result
    return 'Done'
#    return make_response(render_template('succes.html',result=app),200)



def stderr(text,nl='\n'):
    sys.stderr.write(f'{text}{nl}')


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


if __name__ == "__main__":
    app.run()


