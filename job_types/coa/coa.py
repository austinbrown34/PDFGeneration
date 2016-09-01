import sys
import imp
import os
sys.path.append('../..')

from pdfservices import S3TemplateService


def make_number(data):
    try:
        data = float(data)
    except ValueError:
        data = float(0)
    return data


def get_concentration_total(data_list, display_value):
    concentration_total = 0.0
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                concentration_total += make_number(data[analyte]['display'][display_value]['value'])
    return concentration_total


def combine_tests_for_viz(data_list, viz_type, concentration_total=None):
    combined_list = []
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                if viz_type == 'datatable':
                    combined_list.append(
                        [
                            str(analyte),
                            make_number(data[analyte]['display']['%']['loq']),
                            make_number(data[analyte]['display']['%']['value']),
                            make_number(data[analyte]['display']['mg/g']['value'])
                        ]
                    )
                if viz_type == 'sparkline':

                    combined_list.append(
                        [
                            str(analyte),
                            make_number(data[analyte]['display']['%']['value']),
                            make_number(total_concentration)
                        ]
                    )

    return combined_list

def get_test_packages(server_data):
    test_names = []
    for i, package in enumerate(server_data):
        test_names.append(package['name'])
    return test_names


def setup(server_data):

    server_data['viz'] = {}
    viztypes = server_data['viz']
    viztypes['job_type'] = 'coa'
    if 'lab_data_latest' in server_data:
        server_data['lab_data'] = server_data['lab_data_latest']
    if len(server_data['images']) == 0 and server_data['cover'] is None:
        image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
    else:
        if server_data['cover'] is None:
            image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
        else:
            image = 'https:' + server_data['cover']
    server_data['images'] = {}
    server_data['images']['0'] = image
    server_data['cover'] = image
    template_folder = server_data['lab']['abbreviation']
    cannabinoid_data = server_data['lab_data']['cannabinoids']['tests']
    thc_data = server_data['lab_data']['thc']['tests']
    terpenes_data = server_data['lab_data']['terpenes']['tests']
    solvents_data = server_data['lab_data']['solvents']['tests']
    microbials_data = server_data['lab_data']['microbials']['tests']
    mycotoxins_data = server_data['lab_data']['mycotoxins']['tests']
    pesticides_data = server_data['lab_data']['pesticides']['tests']
    metals_data = server_data['lab_data']['metals']['tests']
    total_cannabinoid_concentration = get_concentration_total([cannabinoid_data, thc_data], '%')
    total_terpene_concentration = get_concentration_total([terpenes_data], '%')
    total_solvent_concentration = get_concentration_total([solvents_data], '%')
    total_microbial_concentration = get_concentration_total([microbials_data], '%')
    total_mycotoxin_concentration = get_concentration_total([mycotoxins_data], '%')
    total_pesticide_concentration = get_concentration_total([pesticides_data], '%')
    total_metal_concentration = get_concentration_total([metals_data], '%')
    combined_cannabinoids_dt = combine_tests_for_viz(
        [
            cannabinoid_data,
            thc_data
        ],
        'datatable')
    combined_cannabinoids_sl = combine_tests_for_viz(
        [
            cannabinoid_data,
            thc_data
        ],
        'sparkline',
        total_cannabinoid_concentration)
    terpenes_dt = combine_tests_for_viz(
        [
            terpenes_data
        ],
        'datatable')
    terpenes_sl = combine_tests_for_viz(
        [
            terpenes_data
        ],
        'sparkline',
        total_terpene_concentration)
    solvents_dt = combine_tests_for_viz(
        [
            solvents_data
        ],
        'datatable')
    solvents_sl = combine_tests_for_viz(
        [
            solvents_data
        ],
        'sparkline',
        total_solvent_concentration)
    microbials_dt = combine_tests_for_viz(
        [
            microbials_data
        ],
        'datatable')
    microbials_sl = combine_tests_for_viz(
        [
            microbials_data
        ],
        'sparkline',
        total_microbial_concentration)
    mycotoxins_dt = combine_tests_for_viz(
        [
            mycotoxins_dt
        ],
        'datatable')
    mycotoxins_sl = combine_tests_for_viz(
        [
            mycotoxins_data
        ],
        'sparkline',
        total_mycotoxin_concentration)
    pesticides_dt = combine_tests_for_viz(
        [
            pesticides_data
        ],
        'datatable')
    pesticides_sl = combine_tests_for_viz(
        [
            pesticides_data
        ],
        'sparkline',
        total_pesticide_concentration)
    metals_dt = combine_tests_for_viz(
        [
            metals_data
        ],
        'datatable')
    metals_sl = combine_tests_for_viz(
        [
            metals_data
        ],
        'sparkline',
        total_metal_concentration)
    viztypes['datatable_cannabinoids'] = combined_cannabinoids_dt
    viztypes['sparkline_cannabinoids'] = combined_cannabinoids_sl
    viztypes['datatable_terpenes'] = terpenes_dt
    viztypes['sparkline_terpenes'] = terpenes_sl
    viztypes['datatable_mycotoxins'] = mycotoxins_dt
    viztypes['sparkline_mycotoxins'] = mycotoxins_sl
    viztypes['datatable_microbials'] = microbials_dt
    viztypes['sparkline_microbials'] = microbials_sl
    viztypes['datatable_solvents'] = solvents_dt
    viztypes['sparkline_solvents'] = solvents_sl
    viztypes['datatable_pesticides'] = pesticides_dt
    viztypes['sparkline_pesticides'] = pesticides_sl
    viztypes['datatable_metals'] = metals_dt
    viztypes['sparkline_metals'] = metals_sl



    print "Initializing S3TemplateService"

    if not os.path.exists('/tmp/work'):
        os.makedirs('/tmp/work')
    s3templates = S3TemplateService(bucket='cc-pdfserver')

    print "S3TemplateService initialized"
    def lambda_handler(event, context):
        print "made it to the lambda handler"
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        if not key.endswith('/'):
            try:
                split_key = key.split('/')
                file_name = split_key[-1]
                s3templates.s3.meta.client.download_file(
                    bucket_name,
                    key,
                    '/tmp/work/config.yaml'
                )
            except Exception as e:
                print str(e)
        return (bucket_name, key)
    try:
        s3templates.download_config(
            os.path.join('coa', template_folder),
            'config.yaml',
            '/tmp/work/config.yaml'
        )
    except Exception as e:
        print str(e)
        return

    print "downloaded config"
    template_keys = get_test_packages(server_data['test_packages'])
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    print "getting scripts"
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "downloading templates"
        s3templates.download_templates(os.path.join('coa', template_folder), templates)
        print "downloading scripts"
        s3templates.download_scripts(os.path.join('coa', template_folder), scripts)
    except Exception as e:
        print str(e)
        print str(os.listdir('/tmp'))
        return

    data = server_data
    for script in scripts:
        job = imp.load_source(
            '',
            os.path.join('/tmp', 'work', script))
        data = job.run(data)
    response = {
        'templates': templates,
        'data': data
    }

    print "made it to the end of this section......................................."
    return response
