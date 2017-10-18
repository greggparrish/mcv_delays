import os
import json
import logging
import requests
from requests.exceptions import ConnectionError, ReadTimeout, HTTPError, Timeout
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys
import time
import unittest


TRANSPORT_APP_ID = os.environ['T_ID']
TRANSPORT_API_KEY = os.environ['T_KEY']
STATION = 'MCV'

GROK_HOST = os.environ['G_HOST']
GROK_KEY = os.environ['G_KEY']

TRANSPORT_URI = 'https://transportapi.com/v3/uk/train/station/{}/live.json?app_id={}&app_key={}&darwin=false&train_status=passenger'.format(
    STATION, TRANSPORT_APP_ID, TRANSPORT_API_KEY)

""" Turn off unverified HTTPS request warnings during dev """
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class MCVDelays:

    def __init__(self, *args, **kwargs):
        self.grok_uri = 'https://{}:@{}/'.format(GROK_KEY, GROK_HOST)
        self.metric_name = 'mcv_delays'

    def connect_api(self, uri):
        """ Request json from api, catch errors """
        try:
            r = requests.get(uri, verify=False)
            if r.status_code in [200, 201]:
                return r.text
        except (ConnectionError, HTTPError, ReadTimeout, Timeout) as e:
            """ We could retry based on error, but for now just log them """
            logging.error("CONNECTION ERROR. {}".format(e))
            return False

    def format_data(self, r):
        """ Create payload dict from API response
                return delay_count """
        if 'departures' in r:
            trains = json.loads(r)
            try:
                dd = sum(
                    t['status'] == 'LATE' for t in trains['departures'].get(
                        'all', ''))
                return dd
            except BaseException:
                logging.error(
                    "FORMATTING ERROR. JSON response missing transport status fields")
                return False
        else:
            logging.error(
                "FORMATTING ERROR. Malformed JSON response -- {}".format(r))
            return False

    def send_train_data(self, delay_count):
        """ Send MCV train delay count data to Grok """
        try:
            r = requests.post(
                "{}_metrics/custom/{}".format(
                    self.grok_uri, self.metric_name), json={
                    "value": delay_count, "timestamp": int(
                        time.time())}, verify=False)
        except Exception as e:
            logging.error("POSTING ERROR. Can't post to Grok: {}".format(e))
            return False

        if r.status_code in [200, 201]:
            logging.info("New data posted: {}".format(time.ctime()))
            return True
        else:
            logging.error("POSTING ERROR. Data: {}".format(r.text))
            return False

    def analyze_model(self):
        """ Enable data analysis on mcv_delay metric"""
        try:
            r = self.connect_api('{}/_metrics/custom/'.format(self.grok_uri))
        except Exception as e:
            logging.error(
                "CONNECTION ERROR. Can't connect to Grok: {}".format(e))
            return False
        if r:
            for m in json.loads(r):
                model = {
                    "datasource": "custom",
                    "metricSpec": {
                        "uid": m['uid'],
                        "resource": self.metric_name,
                        "unit": "%"
                    }
                }
            try:
                r = requests.post( "{}_models".format(self.grok_uri),
                    json=model, verify=False)
            except Exception as e:
                logging.error(
                    "CONNECTION ERROR. Can't post analysis to Grok: {}".format(e))
            if r.status_code in [200, 201]:
                logging.info("Analysis enabled")
                return True
            else:
                logging.info("Analysis failed")
                return False


class MCVTests(unittest.TestCase):

    def setUp(self):
        self.test_mcv = MCVDelays()

    def test_transport_api_connection(self):
        """ Test Transport API for valid response and data """
        t = self.test_mcv.connect_api(TRANSPORT_URI)
        self.assertIn('station_code', t)

    def test_grok_api_connection(self):
        """ Test Grok API for valid response """
        r = requests.get(
            'https://{}:@{}/_metrics/custom/'.format(GROK_KEY, GROK_HOST), verify=False)
        self.assertEqual(r.status_code, 200)

    def test_invalid_uri(self):
        """ Test connect_api with an invalid uri """
        self.assertEqual(self.test_mcv.connect_api(
            'https://transportapi'), False)

    def test_inapplicable_json_response(self):
        """ Test format_data with useless json response"""
        r = json.dumps({"user": 1, })
        self.assertEqual(self.test_mcv.format_data(r), False)

    def test_missing_json_fields(self):
        """ Test format_data with a json response that has missing fields,
        should return valid but empty json"""
        r = json.dumps({"departures": 1, "code": 1})
        self.assertEqual(False, self.test_mcv.format_data(r))


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(
        description='Stream Manchester Victoria Station train delays to a Grok instance')
    p.add_argument('-a', '--analyze', help='Enable data analysis',
        action='store_true')
    p.add_argument('-s', '--stream', help='Start stream', action='store_true')
    p.add_argument('-t', '--test', help='Run tests', action='store_true')
    p.add_argument('-v', '--verbose', help='Show info and error messages',
        action='store_true')
    args = p.parse_args()

    mcv = MCVDelays()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    if args.analyze:
        logging.info("++ ANALYSIS: Starting data analysis")
        mcv.analyze_model()
        sys.exit()

    if args.test:
        logging.info("++ TEST: Running test suite")
        suite = unittest.TestLoader().loadTestsFromTestCase(MCVTests)
        unittest.TextTestRunner().run(suite)
        sys.exit()

    if args.stream:
        logging.info("++ STREAM: Starting streaming session")
        st = time.time()
        while True:
            delay_count = 0
            """ Get train data early to give time for slow API connection """
            time.sleep(270)
            r = mcv.connect_api(TRANSPORT_URI)
            if r:
                delay_count = mcv.format_data(r)

            """ Post to Grok, account for drift """
            time.sleep(300 - ((time.time() - st) % 300))
            mcv.send_train_data(delay_count)
