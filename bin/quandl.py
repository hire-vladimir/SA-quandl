# /usr/bin/env python
welcomeText = '''#
# hire.vladimir@gmail.com
#
# allows dataset pulls from quandl.com into Splunk
# developed for use with v3 API version
#
# rev. history
# 8/23/15 1.0 initial write
#
'''
from urllib2 import urlopen, Request, HTTPError
import time, os, re, json
import logging, logging.handlers
import splunk.Intersplunk as si

#######################################
# SCRIPT CONFIG
#######################################
# set log level valid options are: (NOTSET will disable logging)
# CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
SPLUNK_HOME = "."
LOG_LEVEL = logging.INFO
LOG_FILE_NAME = "quandl.log"

# QUANDL specific setings
QUANDL_AUTH_TOKEN = ""


def setup_logging():  # setup logging
    global SPLUNK_HOME, LOG_LEVEL, LOG_FILE_NAME
    if 'SPLUNK_HOME' in os.environ:
        SPLUNK_HOME = os.environ['SPLUNK_HOME']

    log_format = "%(asctime)s %(levelname)-s\t%(module)s[%(process)d]:%(lineno)d - %(message)s"
    logger = logging.getLogger('v')
    logger.setLevel(LOG_LEVEL)

    l = logging.handlers.RotatingFileHandler(os.path.join(SPLUNK_HOME, 'var', 'log', 'splunk', LOG_FILE_NAME), mode='a', maxBytes=1000000, backupCount=2)
    l.setFormatter(logging.Formatter(log_format))
    logger.addHandler(l)

    # ..and (optionally) output to console
    logH = logging.StreamHandler()
    logH.setFormatter(logging.Formatter(fmt=log_format))
    # logger.addHandler(logH)

    logger.propagate = False
    return logger


def getDataPayload(uri):
    logger.debug("Request uri=\"%s\"" % uri)
    payload = ""
    try:
        payload = urlopen(Request(uri)).read()
        logger.debug('Received payload="%s"' % payload)
    except HTTPError, e:
        die('HTTP exception was thrown while making request for uri="%s", status_code=%s, for list of Quandl status codes see https://www.quandl.com/docs/api?json#http-codes e="%s"' % (uri, e.code, e))

    logger.info('function="getDataPayload" action="success" request="%s", bytes_in="%s"' % (uri, len(payload)))
    return payload


def die(msg):
    logger.error(msg)
    exit(msg)


def quandl2splunk(quandl_data, show_info=False, convert_time=True):
    payload = []
    quandl_code = "%s/%s" % (quandl_data['dataset']['database_code'], quandl_data['dataset']['dataset_code'])
    headers = quandl_data['dataset']['column_names']

    if show_info is True:
        row = {"column_names": [h.replace(" ", "_") for h in headers]}
        for field in ['id', 'dataset_code', 'database_code', 'name', 'description', 'refreshed_at', 'newest_available_date', 'oldest_available_date', 'frequency', 'type', 'premium', 'database_id']:
            row[field] = quandl_data['dataset'][field]
        payload.append(row)
    else:
        for r in range(0, len(quandl_data['dataset']['data'])):
            row = {"quandl_code": quandl_code}
            d = quandl_data['dataset']['data'][r]

            for x in range(0, len(headers)):
                h = headers[x].replace(" ", "_")
                row[h] = d[x]
                if convert_time and (h in ['Date', 'Year', 'Month'] and re.match("^\d{4}-\d{2}-\d{2}$", d[x])):
                    row['_time'] = time.mktime(time.strptime(d[x], "%Y-%m-%d"))  # derive epoc from date

            payload.append(row)
    logger.debug('quandl2splunk data="%s"' % payload)

    return payload


def validate_args(keywords, argvals):
    logger.info('function="validate_args" calling getKeywordsAndOptions keywords="%s" args="%s"' % (str(keywords), str(argvals)))

    # validate args
    ALLOWED_OPTIONS = ['debug', 'metadata', 'convert_time', 'auth_token', 'limit', 'rows', 'column_index', 'start_date', 'end_date', 'order', 'collapse', 'transform']
    # MANDATORY_OPTIONS = ['dest']

    for opt in argvals:
        allowed_is_found = False
        for valid in ALLOWED_OPTIONS:
            if (opt == valid):
                allowed_is_found = True
        if allowed_is_found is False:
            die("The argument '%s=%s' is invalid. Supported argumets are: %s" % (opt, argvals[opt], ALLOWED_OPTIONS))

    # validate keywords
    if len(keywords) > 1:
        die("more then one argument specified; see command for usage details")
    if len(keywords) != 1 or not re.match("^\w+\/(?:\([\w,\|\s]+\)|\w+)$", keywords[0]):
        die("dataset not specified, or does not match 'database/dataset' format; if you are using complex dataset definition, ie. database/(dataset1, dataset2) ensure its surronded by quotes")


def make_arg_sub_based_results(argvals, splunk_data):
    for r in argvals:
        for a in splunk_data[0]:  # assumption to use data from first row.. might need to enhance in future
            if argvals[r] == a:
                logger.debug("found substitution oppty, setting %s=%s" % (r, splunk_data[0][a]))
                argvals[r] = splunk_data[0][a]
    logger.debug("function=make_arg_sub_based_results effective args=\"%s\"" % str(argvals))
    return argvals


def arg_on_and_enabled(argvals, arg, rex=None, is_bool=False):
    result = False

    if is_bool:
        rex = "^(?:t|true|1|yes)$"

    if (rex is None and arg in argvals) or (arg in argvals and re.match(rex, argvals[arg])):
        result = True
    return result

if __name__ == '__main__':
    logger = setup_logging()
    logger.info('starting..')
    eStart = time.time()
    try:

        results = si.readResults(None, None, False)
        keywords, argvals = si.getKeywordsAndOptions()
        validate_args(keywords, argvals)

        if results is not None and len(results) > 0:
            argvals = make_arg_sub_based_results(argvals, results)

        # if api_key argument is passed to command, use it instead of default
        if arg_on_and_enabled(argvals, "auth_token"):
            QUANDL_AUTH_TOKEN = argvals["auth_token"]
            logger.debug('setting QUANDL_AUTH_TOKEN="%s"' % str(QUANDL_AUTH_TOKEN))

        if arg_on_and_enabled(argvals, "debug", is_bool=True):
            logger.setLevel(logging.DEBUG)

        quandl_code = keywords[0]
        quandl_database = quandl_code.split("/")[0]
        quandl_dataset = [quandl_code.split("/")[1]]
        if re.match("^\w+\/(?:\([\w,\|\s]+\)+)$", quandl_code):
            quandl_dataset = re.split(",|\|", quandl_code.split("/")[1].replace(" ", "").strip("()"))
            logger.debug('complex code set detected, will split; quandl_dataset="%s"' % quandl_dataset)
        logger.debug('requested quandl_database="%s" quandl_dataset="%s"' % (quandl_database, quandl_dataset))

        # query parameters
        quandl_parameters = []
        quandl_show_info = False
        quandl_parameters.append("auth_token=%s" % QUANDL_AUTH_TOKEN)
        quandl_supported_parameters = ['limit', 'rows', 'column_index', 'start_date', 'end_date', 'order', 'collapse', 'transform']
        for q in quandl_supported_parameters:
            if q in argvals:
                quandl_parameters.append("%s=%s" % (q, argvals[q]))
        logger.debug('quandl_parameters="%s"' % '&'.join(quandl_parameters))

        uber = []
        for set in quandl_dataset:
            # will submit this to quandl
            quandl_uri = "https://www.quandl.com/api/v3/datasets/%s/%s.json?%s" % (quandl_database, set, '&'.join(quandl_parameters))

            if arg_on_and_enabled(argvals, "metadata", is_bool=True):
                logger.info('arg=metadata is set to true, will return feed metadata only; will ignore all other arguments/settings')
                quandl_show_info = True
                quandl_uri = "https://www.quandl.com/api/v3/datasets/%s/%s/metadata.json" % (quandl_database, set)
            logger.debug('effective uri="%s"' % quandl_uri)

            create_time = True
            if arg_on_and_enabled(argvals, "convert_time", rex="^(?:f|false|0|no)$"):
                create_time = False

            quandl_data = json.loads(getDataPayload(quandl_uri))
            uber += quandl2splunk(quandl_data, quandl_show_info, create_time)
        # keeping all data into single array is waste of memory; need to figure out how to call outputResults multiple times, without adding header each time
        logger.info('sending events to splunk count="%s"' % len(uber))
        si.outputResults(uber)
    except Exception, e:
        logger.error('error while processing events, exception="%s"' % e)
        si.generateErrorResults(e)
        raise Exception(e)
    finally:
        logger.info('exiting, execution duration=%s seconds' % (time.time() - eStart))
