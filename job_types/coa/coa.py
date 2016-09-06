import sys
import imp
import os
sys.path.append('../..')

from pdfservices import S3TemplateService
from collections import OrderedDict
from operator import itemgetter
import yaml

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
                try:
                    concentration_total += make_number(data[analyte]['display'][display_value]['value'])
                except Exception as e:
                    print str(e)
                    print "get_concentration_total exception"
                    concentration_total = 0.0
                    continue
    return concentration_total


def combine_tests_for_viz(data_list, category, viz_type, display_unit='%', display_unit2='mg/g', total_concentration=None):
    combined_list = []
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                if viz_type == 'datatable':
                    status = ''
                    if category in ['microbials', 'solvents', 'mycotoxins', 'pesticides', 'metals']:
                        if 'limit' in data[analyte]['display'][display_unit]:
                            if data[analyte]['display'][display_unit]['limit'] == '':
                                status = 'Tested'
                            else:
                                if make_number(data[analyte]['display'][display_unit]['value']) > make_number(data[analyte]['display'][display_unit]['limit']):
                                    status = 'Fail'
                                else:
                                    status = 'Pass'
                        else:
                            data[analyte]['display'][display_unit]['limit'] = ''
                            status = 'Tested'
                        combined_list.append(
                            [
                                str(data[analyte]['display']['name']),
                                make_number(data[analyte]['display'][display_unit]['limit']),
                                make_number(data[analyte]['display'][display_unit]['value']),
                                status
                            ]
                        )
                    else:
                        combined_list.append(
                            [
                                str(data[analyte]['display']['name']),
                                make_number(data[analyte]['display'][display_unit]['loq']),
                                make_number(data[analyte]['display'][display_unit]['value']),
                                make_number(data[analyte]['display'][display_unit2]['value'])
                            ]
                        )
                if viz_type == 'sparkline':

                    combined_list.append(
                        [
                            str(data[analyte]['display']['name']),
                            make_number(data[analyte]['display'][display_unit]['value']),
                            make_number(total_concentration)
                        ]
                    )

    return combined_list

def high_to_low(tested_analytes, report_units):
    analytes_and_values = {}
    for test in tested_analytes:
        for analyte in test:
            analytes_and_values[str(analyte)] = make_number(test[analyte]['display'][report_units]['value'])
    sorted_analytes_and_values = OrderedDict(sorted(analytes_and_values.items(), key=itemgetter(1), reverse=True))
    return sorted_analytes_and_values.items()



def get_test_packages(server_data):
    test_names = []
    for i, package in enumerate(server_data):
        if 'package_key' not in package:
            package['package_key'] = None
        test_names.append([package['package_key'], package['name']])
    return test_names


def get_aromas():
    aroma_file = open('aromas.yaml')
    aromas = yaml.safe_load(aroma_file)
    aroma_file.close()
    return aromas

def numberize(ordered_tuples, category):
    if category == 'terpenes':
        aromas = get_aromas()
        ordered_and_numbered = {}
        for i, e in enumerate(ordered_tuples):
            smell = ''
            if e[0] in aromas:
                smell = 'https://orders.confidentcannabis.com/assets/img/terpenes/' + aromas[e[0]].lower() + '.png'


            ordered_and_numbered[str(i + 1)] = {}
            ordered_and_numbered[str(i + 1)] = {"name": e[0], "value": e[1], "aroma": smell, "aroma_name": aromas[e[0]]}
    else:
        ordered_and_numbered = {}
        for i, e in enumerate(ordered_tuples):
            ordered_and_numbered[str(i + 1)] = {}
            ordered_and_numbered[str(i + 1)] = {"name": e[0], "value": e[1]}
    return ordered_and_numbered


def setup(server_data):
    server_data['date_received'] = server_data['date_recieved']
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
    qr_base = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl="
    public_profile_base = 'https%3A%2F%2Forders.confidentcannabis.com%2Fadvancedherbal%2F%23!%2Freport%2Fpublic%2Fsample%2F'
    public_key = server_data['public_key']
    server_data['qr_code'] = qr_base + public_profile_base + public_key
    template_folder = server_data['lab']['abbreviation']
    test_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals']
    server_data['category_units'] = {}
    try:
        server_data['client']['full_address'] = str(server_data['client_info']['address_line_1']) + ' ' + str(server_data['client_info']['address_line_2']) + ', ' + str(server_data['client_info']['city']) + ', ' + str(server_data['client_info']['state']) + ' ' + str(server_data['client_info']['zipcode'])
        server_data['lab']['full_address'] = str(server_data['lab']['address_line_1']) + ' ' + str(server_data['lab']['address_line_2']) + ', ' + str(server_data['lab']['city']) + ', ' + str(server_data['lab']['state']) + ' ' + str(server_data['lab']['zipcode'])
        # server_data['lab']['license'] = server_data['lab_license']
        #server_data['page_of_pages'] = ''
        server_data['batch_info'] = 'Batch #: ' + '' + '; Batch Size: ' + str(server_data['initial_weight']) + ' - grams'
        if server_data['date_received'] is None or server_data['date_received'] == 'null':
            date_received = ''
        else:
            date_received = server_data['date_received'].split(',')[1].split(' ')
            date_received = date_received[:-2]
            date_received = date_received[2] + ' ' + date_received[1] + ', ' + date_received[3]
        if server_data['last_modified'] is None or server_data['last_modified'] == 'null':
            last_modified = ''
        else:
            last_modified = server_data['last_modified'].split(',')[1].split(' ')
            last_modified = last_modified[:-2]
            last_modified = last_modified[2] + ' ' + last_modified[1] + ', ' + last_modified[3]
        if server_data['date_completed'] is None or server_data['date_completed'] == 'null':
            date_completed = ''
            expires = ''
        else:
            date_completed = server_data['date_completed'].split(',')[1].split(' ')
            date_completed = date_completed[:-3]
            expires = server_data['date_completed'].split(',')[1].split(' ')
            year = server_data['date_completed'].split(',')[1].split(' ')
            year = year[:-2]
            year = str(year[-1])
            expires = str(expires[:-3]) + ' ' + str(int(year) + 1)
            date_completed = date_completed[2] + ' ' + date_completed[1] + ', '
        server_data['bunch_of_dates'] = 'Ordered: ' + date_received + '; Sampled: ' + last_modified + '; Completed: ' + date_completed + '; Expires: ' + expires
        server_data['type_and_method'] = server_data['type']['name'] + ', ' + server_data['method']['name']
        server_data['lab']['full_street_address'] = server_data['lab']['address_line_1'] + ' ' + server_data['lab']['address_line_2']
        server_data['lab']['city_state_zip'] = server_data['lab']['city'] + ', ' + server_data['lab']['state'] + ' ' + server_data['lab']['zipcode']
    except Exception as e:
        print str(e)
        print "this is a concat section issue"
    for category in test_categories:
        print "we're on category ------------------->  " + category
        try:
            report_units = server_data['lab_data'][category]['report_units']
            secondary_report_units = ''
            if report_units == 'mg/g':
                secondary_report_units = '%'
            if report_units == '%':
                secondary_report_units = 'mg/g'
            if category == 'cannabinoids':
                cbd_data = server_data['lab_data']['cannabinoids']['tests']
                thc_data = server_data['lab_data']['thc']['tests']
                ordered = high_to_low([cbd_data, thc_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data[category + '_ordered'] = {}
                server_data[category + '_ordered'] = ordered_and_numbered
                print "server_data[category + '_ordered']:"
                print server_data[category + '_ordered']
                cannabinoid_data = server_data['lab_data']['cannabinoids']['tests']
                print "cannabinoid_data"
                print cannabinoid_data
                total_cannabinoid_concentration = get_concentration_total([cannabinoid_data, thc_data], str(report_units))
                print "total_cannabinoid_concentration"
                print total_cannabinoid_concentration
                print "report_units"
                print report_units
                combined_cannabinoids_dt = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'datatable', report_units, secondary_report_units)
                print "combined cannabinoid dt"
                combined_cannabinoids_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'sparkline', report_units, secondary_report_units,
                    total_concentration=total_cannabinoid_concentration)
                print "combined cannabinoid sl"
                viztypes['datatable_cannabinoids'] = combined_cannabinoids_dt
                viztypes['sparkline_cannabinoids'] = combined_cannabinoids_sl
                server_data['category_units'][category] = [
                    report_units,
                    secondary_report_units
                ]
            elif category == 'microbials':
                print "----------------------------------------------------------------"
                print server_data['lab_data'][category]
                print "----------------------------------------------------------------"
                category_data = server_data['lab_data'][category]['tests']
                ordered = high_to_low([category_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data[category + '_ordered'] = {}
                server_data[category + '_ordered'] = ordered_and_numbered
                print "server_data[category + '_ordered']:"
                print server_data[category + '_ordered']
                print "yay for category data"
                total_category_concentration = get_concentration_total([category_data], str(report_units))
                print "yay for total_category_concentration"
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', report_units, secondary_report_units)
                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', report_units, secondary_report_units,
                    total_concentration=total_category_concentration
                )
                print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                server_data['category_units'][category] = [
                    report_units,
                    secondary_report_units
                ]
            else:
                category_data = server_data['lab_data'][category]['tests']

                print "yay for category data"
                ordered = high_to_low([category_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data[category + '_ordered'] = {}
                server_data[category + '_ordered'] = ordered_and_numbered
                print "server_data[category + '_ordered']:"
                print server_data[category + '_ordered']
                total_category_concentration = get_concentration_total([category_data], str(report_units))
                print "yay for total_category_concentration"
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', report_units, secondary_report_units)
                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', report_units, secondary_report_units,
                    total_concentration=total_category_concentration
                )
                print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                server_data['category_units'][category] = [
                    report_units,
                    secondary_report_units
                ]
        except Exception as e:
            print "made it to the coa exception"
            print str(e)
            continue

    server_data['viz'] = viztypes
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
    lab_logo = s3templates.get_logo('/tmp/work/config.yaml')
    server_data['lab_logo'] = lab_logo
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
