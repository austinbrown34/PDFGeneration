import imp


class PDFJobManager(object):
    def __init__(self, job_type, server_data):
        try:
            job = imp.load_source(
                job_type,
                'JobTypes/' + job_type + '.py')
            response = self.get_instructions(job, server_data)
        except Exception as e:
            response = {
                'status': 'Issue loading job.',
                'error': str(e)
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
