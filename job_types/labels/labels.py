# -*- coding: utf-8 -*
# python 2

import sys
import imp
import os
sys.path.append('../..')
import collections
import time
import shutil
from pdfservices import S3TemplateService, TemplateService
from pdfservices import TemplateService
from collections import OrderedDict
from operator import itemgetter
import yaml
from decimal import *
import copy
from random import *
import json
import random
import requests


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_test_packages(server_data):
    test_names = []
    for i, package in enumerate(server_data):
        package = {'name': package, 'package_key': ''}
        if 'package_key' not in package:
            package = set_value('package_key', None, package)
        test_names.append([value_for('package_key', package), value_for('name', package)])
    return test_names

def value_for(endpoint, data, default='', encoding=None):
    new_data = copy.deepcopy(data)
    points = endpoint.split('.')
    value = ''
    for i, e in enumerate(points):
        if e in new_data:
            new_data = new_data[e]
            value = new_data
        else:
            value = default
            break
    if encoding is not None:
        value = value.encode(encoding)
    return value

def set_value(endpoint, value, data, initial=True):
    if initial:
        current_data = copy.deepcopy(data)
    else:
        current_data = data
    points = endpoint.split('.')
    if len(points) < 2:
        current_data[points[0]] = value
    else:
        for i, e in enumerate(points):
            if e not in current_data or not isinstance(current_data[e], collections.Mapping):
                current_data[e] = {}
            slicer = (i + 1)
            sliced_points = points[slicer:]
            new_endpoint = '.'.join(sliced_points)
            set_value(new_endpoint, value, current_data[e], initial=False)

    return current_data

def make_number(data, digits=None, labels=False):
    try:
        new_data = copy.deepcopy(data)
        new_data = float(new_data)
    except ValueError:
        if new_data == "<LOQ":
            new_data = "&ltLOQ"
        if not labels:
            new_data = float(0)

    output = new_data
    if digits is not None and isinstance(new_data, float):
        quantizer = '1.'
        # print "digits:"
        # print digits
        if int(digits) > 0:
            zeros = '.'
            for i in range(int(digits - 1)):
                zeros += '0'
            quantizer = zeros + '1'
        dec = Decimal(new_data).quantize(Decimal(quantizer))
        # print "decimal is: "
        # print dec
        output = str(dec)
        # output = float(round(dec, digits))
        # print "float is: "
        # print output
    if not labels:
        output = float(output)
    return output

def setup(server_data):
    # print value_for('sample_labels', server_data)
    print bcolors.BOLD
    print "--------------------------------------"
    print "Running Setup for Job Type: LABELS"
    print "--------------------------------------"
    print bcolors.ENDC
    template_folder = value_for('lab.abbreviation', server_data)
    print bcolors.OKBLUE
    print "Preparing Labels for " + template_folder + '...'
    print bcolors.ENDC
    strain_name = value_for('strain_name', server_data)
    # new_strain_name = repr(strain_name)
    print strain_name
    new_strain_name = u' '.join(strain_name).strip()
    # new_strain_name = u' '.join(strain_name).decode().encode('utf-8').strip()

    # new_strain_name = strain_name.decode('UTF-16BE').encode("utf-8")
    print new_strain_name
    server_data = set_value('strain_name', new_strain_name, server_data)
    print "Setting up Preformatted Values..."
    server_data = set_value('viz', {}, server_data)
    viztypes = server_data['viz']
    viztypes['job_type'] = 'labels'
    server_data = set_value('lab_data', value_for('lab_data_latest', server_data), server_data)

    qr_base = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl="
    lab_slug = value_for('lab.slug', server_data)
    public_profile_base = 'https://share.confidentcannabis.com/samples/public/share/'
    public_key = value_for('public_key', server_data)
    print "Formatting QR Code..."
    server_data = set_value('qr_code', public_profile_base + public_key, server_data)


    test_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals']
    server_data = set_value('category_units', {}, server_data)

    months = {
        'Jan': '01',
        'Feb': '02',
        'Mar': '03',
        'Apr': '04',
        'May': '05',
        'Jun': '06',
        'Jul': '07',
        'Aug': '08',
        'Sep': '09',
        'Oct': '10',
        'Nov': '11',
        'Dec': '12'
    }


    print "Formatting Date Completed..."
    server_data = set_value('date_completed', str(time.strftime("%m/%d/%Y")), server_data)
    date_completed = value_for('date_completed', server_data)
    special_category = ''
    special_type = ''
    special_production = ''

    special_category = value_for('category.name', server_data)
    special_type = value_for('type.name', server_data)
    special_production = value_for('method.name', server_data)
    category_type_production = ''
    if special_category != '':
        category_type_production = str(special_category) + ', '
    if special_type != '':
        category_type_production += str(special_type) + ', '
    if special_production != '':
        category_type_production += str(special_production)


    type_and_method = str(value_for('type.name', server_data)) + ', ' + str(value_for('method.name', server_data))
    print "Formatting Type/Method..."
    server_data = set_value('type_and_method', type_and_method, server_data)


    r_units = value_for('lab_data.cannabinoids.report_units', server_data)
    digits = value_for('lab_data.cannabinoids.digits', server_data)
    # special_total_cannabinoids = get_total_cannabinoids([value_for('lab_data.cannabinoids.tests', server_data), value_for('lab_data.thc.tests', server_data)], r_units, digits, display=True)
    special_cbd_total = str(value_for('lab_data.cannabinoids.cbd_total.display.' + str(r_units) + '.value', server_data))
    new_unit = str(r_units)
    if r_units != '%':
        new_unit = ' ' + r_units
    if special_cbd_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
        special_cbd_total = make_number(special_cbd_total, digits, labels=True)
        special_cbd_total = str(special_cbd_total)
        special_cbd_total = special_cbd_total + str(new_unit)
    special_thc_total = str(value_for('lab_data.thc.thc_total.display.' + r_units + '.value', server_data))
    if special_thc_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
        special_thc_total = make_number(special_thc_total, digits, labels=True)
        special_thc_total = str(special_thc_total)
        special_thc_total = special_thc_total + str(new_unit)


    special_moisture = str(value_for('lab_data.moisture.tests.percent_moisture.display.%.value', server_data))
    if str(special_moisture) != '' and str(special_moisture) not in ['ND', 'NR']:
        moisture_digits = value_for('lab_data.moisture.digits', server_data)
        special_moisture = make_number(special_moisture, moisture_digits, labels=True)
        special_moisture = str(special_moisture)
        special_moisture = str(special_moisture) + '%'



    wa_digits = value_for('lab_data.water_activity.digits', server_data)



    status_map = {
        '-1': 'Not Tested',
        '0': 'In Progress',
        '1': 'Pass',
        '2': 'Fail',
        '3': 'Complete'
        }

    status_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals', 'thc', 'foreign_matter']
    status_value = str(value_for('lab_data.status', server_data))
    # print status_value
    print "Formatting Status Message..."
    server_data = set_value('lab_data_latest.status', str(value_for(status_value, status_map)), server_data)
    # server_data = set_value('cc_logo', 'http://cogni.design/cctests/piecharts/CC-logo-cutout.gif', server_data)
    special = {
        'total_thc': str(special_thc_total),
        'total_cbd': str(special_cbd_total),
        'moisture': str(special_moisture),
        'water_activity': str(make_number(value_for('lab_data.water_activity.tests.aw.value', server_data), wa_digits, labels=True)),
        'safety': str(value_for(status_value, status_map))
    }
    print "Formatting Special Fields (Total THC, Total CBD, Moisture, Total Cannabinoids, Water Activity)..."
    server_data = set_value('special', special, server_data)
    print bcolors.BOLD
    print "--------------------------------------"
    print "Beginning Category Data Modifications"
    print "--------------------------------------"
    print bcolors.ENDC

    test_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals']
    server_data = set_value('category_units', {}, server_data)

    for category in test_categories:
        print "Working on ------------------->  " + category.title()
        try:
            digits = value_for('lab_data.' + category + '.digits', server_data)
            report_units = value_for('lab_data.' + category + '.report_units', server_data)
            secondary_report_units = 'mg/g'

            if report_units == 'mg/g':
                secondary_report_units = '%'
            if report_units == '%':
                secondary_report_units = 'mg/g'
            ru = report_units
            sru = secondary_report_units
            if report_units in ['ppm', 'ppb']:
                ru = report_units.upper()
            if report_units == 'cfu/g':
                ru = 'CFU/g'
            if report_units == 'mg/ml':
                ru = 'mg/mL'
            if secondary_report_units in ['ppm', 'ppb']:
                sru = secondary_report_units.upper()
            if secondary_report_units == 'cfu/g':
                sru = 'CFU/g'
            if secondary_report_units == 'mg/ml':
                sru = 'mg/mL'
            server_data = set_value('category_units.' + category, [ru, sru], server_data)
        except Exception as e:
            pass

        viztypes['datatable_' + category] = [[]]
        viztypes['sparkline_' + category] = [[]]
        viztypes['pietable_' + category] = [[]]
        viztypes['pichart_' + category] = [[]]
        viztypes['colors_' + category] = [[]]

    server_data = set_value('category_units.sample', [value_for('lab_data.cannabinoids.report_units', server_data), value_for('lab_data.cannabinoids.report_units', server_data)], server_data)
    viztypes['qr_sample'] = [[value_for('qr_code', server_data)]]
    server_data = set_value('lab_data_latest', value_for('lab_data', server_data), server_data)
    server_data = set_value('viz', viztypes, server_data)
    server_data = set_value('sample_report_columns', [[]], server_data)
    server_data = set_value('sample_report_columns2', [[]], server_data)
    server_data = set_value('sample_report_columns3', [[]], server_data)
    # print "Initializing S3TemplateService"

    if os.path.exists('/tmp/work'):
        shutil.rmtree('/tmp/work')
    if not os.path.exists('/tmp/work'):
        os.makedirs('/tmp/work')

    if 'run_local' in server_data:
        print bcolors.BOLD
        print "--------------------------------------"
        print "Initializing TemplateService"
        print "--------------------------------------"
        print bcolors.ENDC
        s3templates = TemplateService(server_data['run_local'])
    else:
        print bcolors.BOLD
        print "--------------------------------------"
        print "Initializing S3TemplateService"
        print "--------------------------------------"
        print bcolors.ENDC
        s3templates = S3TemplateService(bucket='cc-pdfserver')

    def lambda_handler(event, context):
        # print "made it to the lambda handler"

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
                print "---------------------------------------"
                print bcolors.FAIL + "Lambda Handler Exception" + bcolors.ENDC
                print str(e)
                print "---------------------------------------"
        return (bucket_name, key)
    try:
        print "Attempting to Download Config..."
        s3templates.download_config(
            os.path.join('labels', template_folder),
            'config.yaml',
            '/tmp/work/config.yaml'
        )
    except Exception as e:
        print "---------------------------------------"
        print bcolors.FAIL + "Template Download Exception" + bcolors.ENDC
        print str(e)
        print "---------------------------------------"
        return

    print "Successfully Downloaded Config..."
    print "Labels Found:"
    # print server_data['sample_labels']
    print value_for('sample_labels', server_data)
    template_keys = get_test_packages(value_for('sample_labels', server_data))
    print "Finding Templates for the Labels..."
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    # print "--------------------------------------"
    print "Matched Templates:"
    templates = list(set(templates))
    templates.sort()
    print templates
    # print "--------------------------------------"
    # print "Retrieving Logo..."
    # lab_logo = s3templates.get_logo('/tmp/work/config.yaml')
    # server_data['lab_logo'] = lab_logo
    print "Finding Special Scripts..."
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "Downloading Matched Templates..."
        # print str(templates)
        s3templates.download_templates(os.path.join('labels', template_folder), templates)
        print "Downloading Special Scripts..."
        s3templates.download_scripts(os.path.join('labels', template_folder), scripts)
    except Exception as e:
        print "---------------------------------------"
        print str(e)
        print bcolors.FAIL + "Downloading Templates/Scripts Exception" + bcolors.ENDC
        print "---------------------------------------"
        # print str(os.listdir('/tmp'))
        return

    data = server_data
    for script in scripts:
        job = imp.load_source(
            '',
            os.path.join('/tmp', 'work', script))
        print "--------------------------------------"
        print "Running " + script
        print "--------------------------------------"
        response = job.run(data, templates, s3templates)
        data = response['data']
        templates = response['templates']
    response = {
        'templates': templates,
        'data': data
    }
    # print "these are the templates: "
    # print str(templates)
    print bcolors.BOLD
    print "--------------------------------------"
    print "Finished Preparing Data for Labels"
    print "--------------------------------------"
    print bcolors.ENDC
    # print str(data)
    return response
