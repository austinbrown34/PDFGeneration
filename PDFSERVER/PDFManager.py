from PDFJobManager import PDFJobManager
from PDFMaker import PDFMaker
import boto3
import requests


class PDFManager(object):

    def __init__(self, payload):
        self.payload = payload
        self.job_type = payload['job_type']
        self.delivery_method = payload['delivery_method']
        self.callback = payload['post_data']
        self.server_data = payload['server_data']
        self.redirect_url = payload['redirect_url']
        self.api_key = payload['api_key']
        self.api_secret = payload['api_secret']
        self.status = ''
        self.error = None

    def get_job(self, job_type=None, server_data=None):
        if job_type is None:
            job_type = self.job_type
        if server_data is None:
            server_data = self.server_data
        feedback = PDFJobManager(job_type, server_data)
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
        pdf_response = pdf.make()
        self.status = pdf_response['status']
        if 'error' in pdf_response:
            self.error = pdf_response['error']
            response = self.report_failure()
        else:
            if self.delivery_method == 'POST_FILE':
                response = self.deliver_pdf_file(pdf_response['pdf'])
            if self.delivery_method == 'POST_LINK':
                response = self.deliver_pdf_link(pdf_response['pdf'])

        return response

    def get_url(self, server_url, suffix):
        return '{}/{}'.format(server_url, suffix.strip('\/'))

    def deliver_pdf_file(
            self,
            pdf,
            callback=None,
            redirect_url=None,
            api_key=None,
            api_secret=None):
        if callback is None:
            callback = self.callback
        if redirect_url is None:
            redirect_url = self.redirect_url
        if api_key is None:
            api_key = self.api_key
        if api_secret is None:
            api_secret = self.api_secret
        url = callback['url']
        fields = callback['fields']
        file_key = callback['key']
        try:
            requests.post(
                url,
                data=fields,
                files={
                    'file': pdf
                }
            )
            requests.post(
                self.get_url(url, redirect_url),
                dict(key=file_key),
                api_key,
                api_secret
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

    def deliver_pdf_link(
            self,
            pdf,
            callback=None,
            redirect_url=None,
            api_key=None,
            api_secret=None):
        if redirect_url is None:
            redirect_url = self.redirect_url
        if callback is None:
            callback = self.callback
        if api_key is None:
            api_key = self.api_key
        if api_secret is None:
            api_secret = self.api_secret
        url = callback['url']
        session = boto3.Session(
            aws_access_key_id='AKIAI5NYJC5SDJ3NKVIQ',
            aws_secret_access_key='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'
        )
        s3 = session.resource('s3')
        saved_pdf = file('finalpdf.pdf', 'w')
        saved_pdf.write(pdf.read())
        saved_pdf.close()
        s3.meta.client.upload_file(
            'finalreport.pdf', 'pdfserver', 'finalreport.pdf'
        )
        client = session.client('s3')
        file_url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': 'pdfserver',
                'Key': 'finalreport.pdf'
            }
        )
        try:
            requests.post(
                self.get_url(url, redirect_url),
                dict(url=file_url),
                api_key,
                api_secret
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
