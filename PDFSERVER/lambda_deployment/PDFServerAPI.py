from flask import Flask, jsonify, make_response, request, abort
from PDFManager import PDFManager

app = Flask(__name__)
import sys
import json
import os

app.config['PROPAGATE_EXCEPTIONS'] = True

def unhandled_exceptions(e, event, context):
    print "e:"
    print e
    print "event:"
    print event
    print "context:"
    print context

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/v1/generate', methods=['POST'])
def generate_reports():
    print request
    if not (request.json):
        abort(400)
    print "this is request.json"
    if not os.path.exists('/tmp'):
        os.makedirs('/tmp')
    with open('/tmp/fullpost.txt', 'w') as p:
        p.write(str(request.json))
    print "wrote to some files"
    pdf = PDFManager(request.json)
    print "pdfmanager initialized"
    response = pdf.get_job()

    return jsonify(response)


@app.route('/')
def hello_world():
    return 'Hello Worlds, Welcome to Dynamic PDF Generation!'

if __name__ == '__main__':
    app.run()
