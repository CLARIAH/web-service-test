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
import tempfile
import yaml
from saxonche import PySaxonProcessor, PyXdmValue, PySaxonApiError
from werkzeug.utils import secure_filename
from typing import List
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_pyoidc.user_session import UserSession
from pyfat.fip.testresult import TestResult, MetricResult, Modality

app = Flask(__name__)
upload_folder = tempfile.gettempdir()
app.config.update({
    'OIDC_REDIRECT_URI' : os.environ.get('APP_DOMAIN', 'http://localhost') + '/test',
    'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=7).total_seconds(),
    'UPLOAD_FOLDER': upload_folder,
                   'DEBUG': True})

@app.route("/hello")
def hello_world():
    return "Hello, world!"



@app.route('/test/<identifier>', methods=['POST'])
def do_tests(identifier):
#    identifier = request.json.get('identifier')
#    logging.debug(f'test {identifier}')
    #TODO: DONE 1. check that identifier exists in yml
    if not identifier in m_test_ids:
        return f'{identifier} not found!'
    else:
        if 'cmdi' not in request.files:
            return f'cmdi file not found!'
        file = request.files['cmdi']
        filename = secure_filename(file.filename)
        cmdi_record_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(cmdi_record_path)
        stderr(tempfile.gettempdir())
        stderr(f'cmdi_record_path: {cmdi_record_path}')
        stderr(app.config['UPLOAD_FOLDER'])
        stderr(cmdi_record_path.__class__)
        #logging.debug(m_test_ids[identifier])
        with PySaxonProcessor(license=False) as proc:
            test(identifier,m_test_ids[identifier],proc,cmdi_record_path)
            return f'trying {m_test_ids[identifier]} from {identifier} ...'
    #TODO: 2. if 1  = True: run the test
    #TODO: 3. return json result
    return 'Done'
#    return make_response(render_template('succes.html',result=app),200)


def test(identifier,requirements,proc,cmdi_record_path,variables_dict={}):
    logging.debug(f'\t=> Test: {identifier}')
    logging.debug(f'\t=> Test: {requirements}')
    xpproc = proc.new_xquery_processor()
    for k, v in namespaces.items():
        xpproc.declare_namespace(k, v)
        stderr(f'{k}: {v}') 
    xpproc.set_context(file_name=str(cmdi_record_path))
    if requirements[0]["test"].startswith("xpath:"):  # In Xpath handler... TODO: implement logic for different handlers here (i.e: xpath, Python, etc. Factory)
        xslt_result = None  # reset results...
        log = f'Test modality = {requirements[0]["modality"]}'
        xpath_tst = requirements[0]["test"].split("xpath:", 1)[1]
        logging.debug(f'\t\t=> Test: {xpath_tst}, modality: {requirements[0]["modality"]}')
        var_declare_list = []
        var_declare_str = ''
        if requirements[0].get("variables", False):
            stderr(f'contains varia')
            for varia in requirements[0].get("variables"):
                stderr(f'varia: {varia}')
                var_name = varia.split("=", 1)[0]
                var_val = varia.split("=", 1)[1]
                logging.debug(f'\t\t=> Var name={var_name}, value={var_val}')

                varproc = proc.new_xpath_processor()
                varproc.declare_variable("RECORDPATH")
                varproc.set_parameter("RECORDPATH", proc.make_string_value(cmdi_record_path, encoding="UTF-8"))

                for k, v in variables_dict.items():
                    varproc.declare_variable(k)
                    varproc.set_parameter(k, proc.make_string_value(json.dumps(v), encoding="UTF-8"))
                try:
                    json_result = varproc.evaluate(var_val)
                except (RuntimeError, BaseException, PySaxonApiError) as err:
                    logging.error(f"\t\tError executing Xpath test: {var_val}: {err}")
                    exit(1)
                xpproc.set_parameter(var_name, json_result)
                var_declare_list.append(f"declare variable ${var_name} external")
            var_declare_str = '; '.join(var_declare_list) + ";"
            # Add declarations to the output Log:
            if var_declare_str: log = log + ", " + var_declare_str

        logging.info(f"\t\t=> Setting Xquery content on procc: {var_declare_str} {xpath_tst}")
        xpproc.set_query_content(f"{var_declare_str} {xpath_tst}")

        # Run Xpath query
        try:  # Looks like the parser might still print a java.io.IOException, that cannot be caught: FODC0002  I/O error reported by XML parser processing https://curation.clarin.eu/download/profile/clarin_eu_cr1_p_1650879720846. Caused by java.io.IOException: Server returned HTTP response code: 500 for URL: (...)
            xslt_result = xpproc.run_query_to_value(encoding="UTF-8")
        except (RuntimeError, BaseException, PySaxonApiError) as err:
            logging.error(f"\t\tError executing Xpath test: {xpath_tst}: {err}")
        if xslt_result:  # Do not include None results in the metric => TODO: take account for None results (i.e: indeterminate) in the end/total assessment score. For now just skip them.Beware:
            test_result = get_test_result(xslt_result, Modality[metric_test['requirements[0]s'][0]['modality'].upper()], metric_test["metric_test_score"], metric_test["metric_test_identifier"],
                                                          identifier, requirements[0]["test"], log, identifier)
            metric_tst_results_list.append(test_result)
            logging.debug(f'\t\t=> Test Result: {test_result}')
        else:
            logging.warning(f"Test identifier '{identifier}' did NOT yield results!")


    return xslt_result
 

def get_test_result(result_list: List[PyXdmValue], testmodality: Modality, max_tst_score: float, test_id: str, testname: str, testvalue: str, log: str, metricid: str) -> TestResult:
    if not result_list:
        return TestResult(False, 0, test_id, testname, testvalue, log, metricid, datetime.now())  # Fail with 0 score

    if all(isinstance(item, PyXdmValue) and item.string_value in ["true", "false"] for item in result_list):
        if testmodality is Modality.ANY:
            success = any(res.boolean_value for res in result_list)
            score = max_tst_score if success else 0
        elif testmodality is Modality.ALL:
            success = all(res.boolean_value for res in result_list)
            score = max_tst_score if success else 0
        else:  # TODO: Do we allow for a test to return a double value? This probably is a measurement or a benchmark result... How to interpret this? OSTrails test output: Pass, Fail or indeterminate.
            item = result_list[0]
            success = 0 <= item.double_value <= 1
            score = round(item.double_value * max_tst_score, 1) if success else 0
    return TestResult(success, score, test_id, testname, testvalue, log, metricid, datetime.now())




def stderr(text,nl='\n'):
    sys.stderr.write(f'{text}{nl}')


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

metric_ids = []
m_test_ids = {}
namespaces = {}
with open('data/clarin_fip_metrics_v0.3.yaml', 'r') as f:
    data = yaml.load(f, Loader=yaml.SafeLoader)
    metrics = data['metrics'] #['metric_tests']
    for i in range(0,len(metrics)):
        metric_id = metrics[i]['metric_identifier'].split('/')[-1]
        metric_ids.append(metric_id)
        test_list = metrics[i]['metric_tests']
        for j in range(0,len(test_list)):
            m_test_id = test_list[j]['metric_test_identifier']
            m_test_ids[m_test_id ] = test_list[j]['metric_test_requirements']
    namespaces = data['config']['metric_namespaces']



if __name__ == "__main__":
    app.run()


