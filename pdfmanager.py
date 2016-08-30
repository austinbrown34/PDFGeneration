from pdfjobmanager import PDFJobManager
from pdfmaker import PDFMaker
import boto3
import requests
import json
import subprocess

class PDFManager(object):

    def __init__(self, payload):
        self.payload = payload
        self.job_type = payload['job_type']
        self.delivery_method = payload['delivery_method']
        self.callback = payload['post_data']
        self.server_data = payload['pdf_data']
        self.redirect_url = payload['redirect_url']
        self.redirect_url_base = payload['redirect_url_base']
        self.api_key = payload['api_key']
        self.api_secret = payload['api_secret']
        self.status = ''
        self.error = None

    def get_job(self, job_type=None, server_data=None):
        if job_type is None:
            job_type = self.job_type
        if server_data is None:
            server_data = self.server_data


        pdfjob = PDFJobManager(job_type, server_data)
        feedback = pdfjob.load_job()
        self.status = feedback['status']
        if 'error' in feedback:
            self.error = feedback['error']
            response = self.report_failure()
        else:
            details = feedback['details']
            response = self.run_job(details['templates'], details['data'])

        return response

    def report_failure(self):
        message = {
            'status': self.status,
            'error': self.error
        }

        return message

    def run_job(self, templates, data, delivery_method=None):
        if delivery_method is None:
            delivery_method = self.delivery_method
        pdf = PDFMaker(templates, data)
        pdf_response = pdf.make_pages()
        self.status = pdf_response['status']
        if 'error' in pdf_response:
            self.error = pdf_response['error']
            response = self.report_failure()
        else:
            if self.delivery_method == 'POST_FILE':
                response = self.deliver_pdf_file(pdf_response['pdf'])
            if self.delivery_method == 'POST_LINK':
                response = self.deliver_pdf_link(pdf_response['pdf'])
        print str(response)
        return response

    def get_url(self, server_url, suffix):
        return '{}/{}'.format(server_url, suffix.strip('\/'))

    def deliver_pdf_file(
            self,
            pdf,
            callback=None,
            redirect_url=None,
            redirect_url_base=None,
            api_key=None,
            api_secret=None,
            file_key=None):
        if callback is None:
            callback = self.callback
        if redirect_url is None:
            redirect_url = self.redirect_url
        if redirect_url_base is None:
            redirect_url_base = self.redirect_url_base
        if api_key is None:
            api_key = self.api_key
        if api_secret is None:
            api_secret = self.api_secret
        if file_key is None:
            file_key = self.payload['key']
        url = callback['url']
        fields = callback['fields']
        try:
            first = requests.post(
                url,
                data=fields,
                files={
                    'file': pdf
                }
            )
            print "first post info:"
            print url
            print str(fields)
            print first
            this_data = {'key': file_key}
            if api_key and api_secret:
                this_data['API_KEY'] = api_key
                this_data['API_SECRET'] = api_secret
            second = requests.post(
                self.get_url('https://' + redirect_url_base, redirect_url),
                this_data
            )
            print "second post info:"
            print self.get_url(url, redirect_url)
            print second.text
            print callback

            self.status = 'Successfully Generated and Delivered PDF.'
            response = {
                'status': self.status
            }
        except Exception as e:
            self.status = 'Delivery was unsuccessful.'
            self.error = e
            response = {
                'status': self.status,
                'error': str(self.error)
            }

        return response

    def deliver_pdf_link(
            self,
            pdf,
            callback=None,
            redirect_url=None,
            redirect_url_base=None,
            api_key=None,
            api_secret=None):
        if redirect_url is None:
            redirect_url = self.redirect_url
        if redirect_url_base is None:
            redirect_url_base = self.redirect_url_base
        if callback is None:
            callback = self.callback
        if api_key is None:
            api_key = self.api_key
        if api_secret is None:
            api_secret = self.api_secret
        url = callback['url']
        session = boto3.Session()
        s3 = session.resource('s3')
        saved_pdf = file('/tmp/finalpdf.pdf', 'w')
        saved_pdf.write(pdf)
        saved_pdf.close()
        s3.meta.client.upload_file(
            '/tmp/finalpdf.pdf', 'pdfserver', 'finalpdf.pdf'
        )
        client = session.client('s3')
        file_url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': 'pdfserver',
                'Key': 'finalpdf.pdf'
            }
        )
        try:
            this_data = {'url': file_url}
            new_url = self.get_url(redirect_url_base, redirect_url)
            print "Posting to: " + new_url
            if api_key and api_secret:
                this_data['API_KEY'] = api_key
                this_data['API_SECRET'] = api_secret
            headers = {'Content-Type': 'application/json'}
            requests.post(
                new_url,
                data=json.dumps(this_data),
                headers=headers
            )
            self.status = 'Successfully Generated and Delivered PDF.'
            response = {
                'status': self.status
            }
        except Exception as e:
            self.status = 'Delivery was unsuccessful.'
            self.error = e
            response = {
                'status': self.status,
                'error': str(self.error)
            }

        return response
