from flask import Flask, jsonify, make_response, request, abort
from pdfmanager import PDFManager
import shutil

app = Flask(__name__)
import sys
import json
import os


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


app.config['PROPAGATE_EXCEPTIONS'] = True

def unhandled_exceptions(e, event, context):
    print "------------------------------------------"
    print bcolors.FAIL + "Unhandled Exceptions Exception" + bcolors.ENDC
    print "e:"
    print e
    print "event:"
    print event
    print "context:"
    print context
    print "------------------------------------------"

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/v1/generate', methods=['POST'])
def generate_reports():
    # print request
    if not (request.json):
        abort(400)
    # print "this is request.json"
    if os.path.exists('/tmp/Final_PDF_fixed.pdf'):
        os.remove('/tmp/Final_PDF_fixed.pdf')
    if os.path.exists('/tmp/work'):
        shutil.rmtree('/tmp/work')
    if not os.path.exists('/tmp'):
        os.makedirs('/tmp')
    # print str(request.json)
    # print "wrote to some files"
    pdf = PDFManager(request.json)
    print bcolors.BOLD
    print "----------------------------------"
    print "PDFManager Initialized"
    print "----------------------------------"
    print bcolors.ENDC
    response = pdf.get_job()
    # print "made it to the end"
    # ghostdir = os.listdir('/usr/share/fonts/default/ghostscript')
    # print str(ghostdir)
    print response
    return jsonify(response)


@app.route('/')
def hello_world():
    return 'Hello Worlds, Welcome to Dynamic PDF Generation!'

if __name__ == '__main__':
    app.run()
