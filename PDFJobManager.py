import imp
import sys, os


class PDFJobManager(object):
    def __init__(self, job_type, server_data):
        self.job_type = job_type
        self.server_data = server_data

    def load_job(self, job_type=None, server_data=None):
        if job_type is None:
            job_type = self.job_type
        if server_data is None:
            server_data = self.server_data
        try:
            job_type = job_type.lower()
            job = imp.load_source(
                job_type,
                os.path.join('job_types', job_type, job_type + '.py')
                )
            response = self.get_instructions(job, server_data)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            response = {
                'status': 'Issue loading job.',
                'error': str(e) + ',' +
                str(exc_type) +
                ',' +
                str(fname) +
                ',' +
                str(exc_tb.tb_lineno)
            }
        return response

    def get_instructions(self, job, server_data):

        templates_and_data = job.setup(server_data)
        response = {
            'status': 'Job loaded and instructions received.',
            'details': {
                'templates': templates_and_data['templates'],
                'data': templates_and_data['data']
            }
        }
        return response
