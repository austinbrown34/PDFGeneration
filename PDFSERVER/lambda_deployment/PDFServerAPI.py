from flask import Flask, jsonify, make_response, request, abort
from PDFManager import PDFManager

app = Flask(__name__)
import sys

app.config['PROPAGATE_EXCEPTIONS'] = True
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/v1/generate', methods=['POST'])
def generate_reports():
    print "hello"
    if not (request.json):
        abort(400)
    
    with open('log.txt', 'w') as f:
        sys.stdout = f
        pdf = PDFManager(request.json)
        response = pdf.get_job()

    return jsonify(response)


@app.route('/')
def hello_world():
    return 'Hello Worlds, Welcome to Dynamic PDF Generation!'

if __name__ == '__main__':
    app.run()
