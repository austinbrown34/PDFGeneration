# -*- coding: utf-8 -*
# python 2

import sys
import imp
import os
sys.path.append('../..')
import collections
import time
import shutil
from pdfservices import S3TemplateService
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
import re
import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def update_color_list(color_list, filename):
    with open('job_types/coa/viz/piechart/js/colors.js', 'r') as file:
        content = file.readlines()
    content[1] = json.dumps(color_list) + ';\n'
    data_vis_name = 'job_types/coa/viz/piechart/js/' + filename
    data_vis_name_split = data_vis_name.split("/")
    data_vis_name_split.pop()
    data_vis_location = '/tmp/'
    for i, e in enumerate(data_vis_name_split):
        data_vis_location += e + '/'
        if not os.path.isdir(data_vis_location):
            os.makedirs(data_vis_location)
    with open(os.path.join('/tmp', 'job_types', 'coa', 'viz', 'piechart', 'js', filename), 'w') as file:
        file.writelines(content)
    # print "wrote the js file"

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

def get_total_cannabinoids(tests, units, digits, display=False):
    total = 0.0
    for test in tests:
        for analyte in test:
            if 'total' not in analyte:
                value = make_number(value_for(analyte + '.display.' + units + '.value', test), digits)
                total += value
    if display:
        if str(units) == '%':
            total = str(total) + str(units)
        else:
            total = str(total) + ' ' + str(units)
    return total

def formatted_phone(phone):
    formatted_phone = ''
    if phone is not None:
        if len(phone) < 10:
            formatted_phone = phone
        else:
            for i, e in enumerate(phone):
                if i == 0:
                    formatted_phone += '(' + str(e)
                elif i == 2:
                    formatted_phone += str(e) + ') '
                elif i == 6:
                    formatted_phone += '-' + str(e)
                else:
                    formatted_phone += str(e)
    else:
        formatted_phone = ''
    return formatted_phone

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

def get_winner(data_list, display_value):
    highest = 0.0
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                try:
                    value = make_number(value_for(analyte + '.display.' + display_value + '.value', data))
                    if value > highest:
                        highest = value
                except Exception as e:
                    print "------------------------------------------"
                    print bcolors.FAIL + "Get Winner Exception" + bcolors.ENDC
                    print str(e)
                    print "------------------------------------------"
                    continue
    return highest


def format_sparkline_data(sl_data):
    new_sl_data = []
    for i, e in enumerate(sl_data):
        formatted_field = '<progress max="' + str(e[2]) + '" value="' + str(e[1]) + '"></progress>'
        formatted_entry = [e[0], formatted_field]
        new_sl_data.append(formatted_entry)
    return new_sl_data

def get_concentration_total(data_list, display_value):
    concentration_total = 0.0
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                try:
                    concentration_total += make_number(value_for(analyte + '.display.' + display_value + '.value', data))
                except Exception as e:
                    print "------------------------------------------"
                    print bcolors.FAIL + "Get Concentration Total Exception" + bcolors.ENDC
                    print str(e)
                    print "------------------------------------------"
                    # print "get_concentration_total exception"
                    concentration_total = 0.0
                    continue
    return concentration_total

def add_units_to_values(tests):
    # formatted_tests = tests
    formatted_tests = copy.deepcopy(tests)
    for analyte in tests:
        # print analyte
        for display_chunk in value_for(analyte + '.display', tests):
            # print display_chunk
            if display_chunk not in ['name', 'aroma']:
                for value_type in value_for(analyte + '.display.' + display_chunk, tests):
                    # print value_type
                    try:
                        converted_value = float(str(value_for(analyte + '.display.' + display_chunk + '.' + value_type, tests)))
                        dec = Decimal(converted_value).quantize(Decimal(10) ** -2)
                        # dec = Decimal(converted_value)
                        output = dec
                        if str(display_chunk) in ['ppm', 'ppb', 'cfu/g']:
                            output = int(round(dec, 0))
                        new_display_chunk = display_chunk
                        if str(display_chunk) != '%':
                            if str(display_chunk) in ['ppm', 'ppb']:
                                new_display_chunk = ' ' + str(display_chunk).upper()
                            if str(display_chunk) == 'cfu/g':
                                new_display_chunk = ' CFU/g'
                            if str(display_chunk) == 'mg/ml':
                                new_display_chunk = ' mg/mL'
                        units = str(new_display_chunk)
                        formatted_tests = set_value(analyte + '.display.' + display_chunk + '.' + value_type, str(output) + str(units), formatted_tests)
                    except Exception as e:
                        # print "------------------------------------------"
                        # print bcolors.FAIL + "Add Units Exception" + bcolors.ENDC
                        # print str(e)
                        # print "------------------------------------------"
                        # print "made it to the add_units exception"
                        converted_value = str(value_for(analyte + '.display.' + display_chunk + '.' + value_type, tests))
                        formatted_tests = set_value(analyte + '.display.' + display_chunk + '.' + value_type, str(converted_value), formatted_tests)
                        # print "Converterd to: " + str(value_for(analyte + '.display.' + display_chunk + '.' + value_type, formatted_tests))
                        continue

    return formatted_tests

def get_colors(how_many):
    colorlist = []
    cf = open('job_types/coa/colors.yaml')
    colors = yaml.safe_load(cf)
    cf.close()
    counter = 0
    for i in range(how_many):
        if not counter < len(colors['colors']) - 1:
            counter = 0
        color = colors['colors'][counter]
        colorlist.append(color)
        counter += 1

    return colorlist

def resort_colors(color_list, pietable, piechart):
    resorted_color_list = []
    if len(color_list) > 0:
        pietable_key = {}
        for i, e in enumerate(pietable):
            analyte = e[0]
            color = e[3].split('background:')[1].split(';')[0]
            pietable_key[analyte] = color
        for j, k in enumerate(piechart):
            if j != 0:
                analyte = k[0]
                color = pietable_key[analyte]
                resorted_color_list.append(color)
    return resorted_color_list



def combine_tests_for_viz(data_list, category, viz_type, digits, display_unit='%', display_unit2='mg/g', total_concentration=None, color_list=None):
    combined_list = []
    if color_list is None:
        color_list = []
    try:
        special_list = []

        color_counter = 0
        color_counter2 = 0
        datatable_first = True
        datatable_sparkline_first = True
        pietable_first = True

        for d in data_list:
            data = copy.deepcopy(d)


            for a in data:
                analyte = copy.deepcopy(a)
                if 'total' not in analyte or category != "cannabinoids":
                    if viz_type == 'piechart':
                        color = color_list[color_counter2]
                        color_counter2 += 1
                        combined_list.append(
                            [
                                str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits)

                            ]
                        )
                    if viz_type == 'pietable':
                        color = color_list[color_counter]
                        color_counter += 1
                        report_data = [
                                str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                str(make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True)),
                                str(make_number(value_for(analyte + '.display.' + display_unit2 + '.value', data), digits, labels=True)),
                                '<div id="colorkey" class="right" style="background:' + color + ';"></div>'
                            ]
                        if analyte == "thca":
                            # new_list = combined_list[:0] + report_data + combined_list[0:]
                            special_list[0:0] = [report_data]

                        elif analyte == "d9_thc":
                            special_list[1:1] = [report_data]

                        elif analyte == "cbda":
                            special_list[2:2] = [report_data]
                        elif analyte == "cbd":
                            special_list[3:3] = [report_data]
                        else:
                            combined_list.append(
                                report_data
                            )
                    if viz_type == 'datatable_sparkline':
                        status = ''
                        if category in ['microbials', 'solvents', 'mycotoxins', 'pesticides', 'metals']:
                            if 'limit' in value_for(analyte + '.display.' + display_unit, data):
                                if value_for(analyte + '.display.' + display_unit + '.limit', data) == '':
                                    status = 'Tested'
                                else:
                                    if make_number(value_for(analyte + '.display.' + display_unit + '.value', data)) > make_number(value_for(analyte + '.display.' + display_unit + '.limit', data)):
                                        status = 'Fail'
                                    else:
                                        status = 'Pass'
                            else:
                                data = set_value(analyte + '.display.' + display_unit + '.limit', '', data)
                                status = 'Tested'
                            if category not in ['microbials']:
                                combined_list.append(
                                    [
                                        str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.loq', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.limit', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                        status,
                                        '<progress max="' + str(make_number(total_concentration, digits)) + '" value="' + str(make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits)) + '"></progress>'
                                    ]
                                )
                            else:
                                combined_list.append(
                                    [
                                        str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.limit', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                        status,
                                        '<progress max="' + str(make_number(total_concentration, digits)) + '" value="' + str(make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits)) + '"></progress>'
                                    ]
                                )
                            # make_number(data[analyte]['display'][display_unit]['value'], digits),
                            # make_number(total_concentration, digits)
                        else:
                            report_data = [
                                str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                make_number(value_for(analyte + '.display.' + display_unit + '.loq', data), digits, labels=True),
                                make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                make_number(value_for(analyte + '.display.' + display_unit2 + '.value', data), digits, labels=True),
                                '<progress max="' + str(make_number(total_concentration, digits)) + '" value="' + str(make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits)) + '"></progress>'
                            ]

                            if analyte == "thca":
                                # new_list = combined_list[:0] + report_data + combined_list[0:]
                                special_list[0:0] = [report_data]

                            elif analyte == "d9_thc":
                                special_list[1:1] = [report_data]

                            elif analyte == "cbda":
                                special_list[2:2] = [report_data]
                            elif analyte == "cbd":
                                special_list[3:3] = [report_data]
                            else:
                                combined_list.append(
                                    report_data
                                )
                    if viz_type == 'datatable':
                        status = ''
                        if category in ['microbials', 'solvents', 'mycotoxins', 'pesticides', 'metals']:
                            if 'limit' in value_for(analyte + '.display.' + display_unit, data):
                                if value_for(analyte + '.display.' + display_unit + '.limit', data) == '':
                                    status = 'Tested'
                                else:
                                    if make_number(value_for(analyte + '.display.' + display_unit + '.value', data)) > make_number(value_for(analyte + '.display.' + display_unit + '.limit', data)):
                                        status = 'Fail'
                                    else:
                                        status = 'Pass'
                            else:
                                data = set_value(analyte + '.display.' + display_unit + '.limit', '', data)
                                status = 'Tested'
                            if category not in ['microbials']:
                                combined_list.append(
                                    [
                                        str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.loq', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.limit', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                        status
                                    ]
                                )
                            else:
                                combined_list.append(
                                    [
                                        str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.limit', data), digits, labels=True),
                                        make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                        status
                                    ]
                                )
                        else:
                            report_data = [
                                str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                                make_number(value_for(analyte + '.display.' + display_unit + '.loq', data), digits, labels=True),
                                make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits, labels=True),
                                make_number(value_for(analyte + '.display.' + display_unit2 + '.value', data), digits, labels=True)
                            ]

                            if analyte == "thca":
                                # new_list = combined_list[:0] + report_data + combined_list[0:]
                                special_list[0:0] = [report_data]

                            elif analyte == "d9_thc":
                                special_list[1:1] = [report_data]

                            elif analyte == "cbda":
                                special_list[2:2] = [report_data]
                            elif analyte == "cbd":
                                special_list[3:3] = [report_data]
                            else:
                                combined_list.append(
                                    report_data
                                )
                    if viz_type == 'sparkline':

                        report_data = [
                            str(value_for(analyte + '.display.name', data, encoding='utf-8')),
                            make_number(value_for(analyte + '.display.' + display_unit + '.value', data), digits),
                            make_number(total_concentration, digits)
                        ]
                        if analyte == "thca":
                            # new_list = combined_list[:0] + report_data + combined_list[0:]
                            special_list[0:0] = [report_data]

                        elif analyte == "d9_thc":
                            special_list[1:1] = [report_data]

                        elif analyte == "cbda":
                            special_list[2:2] = [report_data]
                        elif analyte == "cbd":
                            special_list[3:3] = [report_data]
                        else:
                            combined_list.append(
                                report_data
                            )
        combined_list = special_list + combined_list
    except Exception as e:
        print "------------------------------------------"
        print bcolors.FAIL + "Combine Tests For Viz Exception" + bcolors.ENDC
        print str(e)
        print "------------------------------------------"
    return combined_list

def add_units_to_tables(table, columns, display_unit, display_unit2):
    units_row = []
    mass_counter = 0
    units = ['mass', 'loq', 'limit', 'spike']
    match = False
    for i, e in enumerate(columns):
        # print display_unit
        for unit in units:
            display_unit = str(display_unit)
            display_unit2 = str(display_unit2)
            # if display_unit == "%%":
            #     display_unit = "%"
            # if display_unit2 == "%%":
            #     display_unit2 = "%"
            if e['title'].lower().find(unit) != -1:
                if unit == "mass" and mass_counter == 0:
                    units_row.append(display_unit)
                    mass_counter += 1
                    match = True
                elif unit == "mass" and mass_counter > 0:
                    units_row.append(display_unit2)
                    match = True
                elif unit == "spike":
                    units_row.append('%')
                    match = True
                else:
                    units_row.append(display_unit)
                    match = True
        if match:
            match = False
        else:
            units_row.append('')
    formatted_units_row = []
    for i, e in enumerate(units_row):
        if e == "%%%%":
            e = "%"
        if e in ['ppm', 'ppb']:
            e = e.upper()
        if e == 'cfu/g':
            e = 'CFU/g'
        if e == 'mg/ml':
            e = 'mg/mL'
        formatted_units_row.append(e)
        # print form
    new_table = table.insert(0, formatted_units_row)

    return new_table

def add_cannabinoid_totals(combined_list, display_unit, display_unit2, digits, combined=False):
    primary_total = 0.0
    secondary_total = 0.0
    for row in combined_list:
        primary = make_number(row[2], digits=digits)
        secondary = make_number(row[3], digits=digits)
        primary_total += primary
        secondary_total += secondary

    primary_total = str(make_number(primary_total, digits=digits, labels=True))
    secondary_total = str(make_number(secondary_total, digits=digits, labels=True))

    if combined:
        combined_list.append(
            [
                'Total',
                '',
                primary_total,
                secondary_total,
                ''
            ]
        )

    else:
        combined_list.append(
            [
                'Total',
                '',
                primary_total,
                secondary_total
            ]
        )

        return combined_list
def high_to_low(tested_analytes, report_units):
    analytes_and_values = {}
    for test in tested_analytes:
        # print test
        for analyte in test:
            analytes_and_values = set_value(str(analyte), make_number(value_for(analyte + '.display.' + report_units + '.value', test)), analytes_and_values)
    sorted_analytes_and_values = OrderedDict(sorted(analytes_and_values.items(), key=itemgetter(1), reverse=True))
    return sorted_analytes_and_values.items()



def get_test_packages(server_data):
    test_names = []
    for i, package in enumerate(server_data):
        if 'package_key' not in package:
            package = set_value('package_key', None, package)
        if 'internal_id' not in package:
            package = set_value('internal_id', None, package)
        test_names.append([value_for('package_key', package), value_for('name', package), value_for('internal_id', package)])
    return test_names


def get_aromas():
    aroma_file = open('aromas.yaml')
    aromas = yaml.safe_load(aroma_file)
    aroma_file.close()
    return aromas

def numberize(ordered_tuples, category):
    if category == 'terpenes':
        aromas = get_aromas()
        # print ordered_tuples
        ordered_and_numbered = {}
        for i, e in enumerate(ordered_tuples):
            smell = ''
            if e[0] in aromas:
                smell = 'https://orders.confidentcannabis.com/assets/img/terpenes/' + aromas[e[0]].lower() + '.png'

            ordered_and_numbered = set_value(str(i + 1), {"name": e[0], "value": e[1], "aroma": smell, "aroma_name": aromas[e[0]]}, ordered_and_numbered)
    else:
        ordered_and_numbered = {}
        for i, e in enumerate(ordered_tuples):
            ordered_and_numbered[str(i + 1)] = {}
            ordered_and_numbered = set_value(str(i + 1), {"name": e[0], "value": e[1]}, ordered_and_numbered)
    return ordered_and_numbered


def setup(server_data):
    print bcolors.BOLD
    print "--------------------------------------"
    print "Running Setup for Job Type: COA"
    print "--------------------------------------"
    print bcolors.ENDC
    template_folder = value_for('lab.abbreviation', server_data)
    print bcolors.OKBLUE
    print "Preparing COA for " + template_folder + '...'
    print bcolors.ENDC
    print bcolors.BOLD
    print "--------------------------------------"
    print "Sample ID: " + value_for('lab_internal_id', server_data)
    print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
    print "--------------------------------------"
    print bcolors.ENDC
    # lab_internal_id = value_for('lab_internal_id', server_data)
    print "Setting up Preformatted Values..."
    server_data = set_value('date_received', value_for('date_recieved', server_data), server_data)
    server_data = set_value('viz', {}, server_data)
    viztypes = server_data['viz']
    viztypes['job_type'] = 'coa'
    server_data = set_value('lab_data', value_for('lab_data_latest', server_data), server_data)
    cover = value_for('cover', server_data)
    if cover == '' or cover is None:
        image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
    else:
        image = 'https:' + cover
    server_data = set_value('cover', image, server_data)
    qr_base = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl="
    lab_slug = value_for('lab.slug', server_data)
    public_profile_base = 'https%3A%2F%2Forders.confidentcannabis.com%2F' + str(lab_slug) + '%2F%23!%2Freport%2Fpublic%2Fsample%2F'
    public_key = value_for('public_key', server_data)
    print "Formatting QR Code..."
    server_data = set_value('qr_code', qr_base + public_profile_base + public_key, server_data)


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
    client_phone = value_for('client_info.phone', server_data)
    print "Formatting Client Phone..."
    server_data = set_value('formatted_client_phone', formatted_phone(client_phone), server_data)
    lab_phone = value_for('lab.phone', server_data)
    print "Formatting Lab Phone..."
    server_data = set_value('formatted_lab_phone', formatted_phone(lab_phone), server_data)
    client_address_1 = value_for('client_info.address_line_1', server_data)
    client_address_2 = value_for('client_info.address_line_2', server_data)
    client_city = value_for('client_info.city', server_data)
    client_state = value_for('client_info.state', server_data)
    client_zipcode = value_for('client_info.zipcode', server_data)
    client_full_address = str(client_address_1) + ' ' + str(client_address_2) + ', ' + str(client_city) + ', ' + str(client_state) + ' ' + str(client_zipcode)
    print "Formatting Client Address..."
    server_data = set_value('client.full_address', client_full_address, server_data)
    lab_address_1 = value_for('lab.address_line_1', server_data)
    lab_address_2 = value_for('lab.address_line_2', server_data)
    lab_city = value_for('lab.city', server_data)
    lab_state = value_for('lab.state', server_data)
    lab_zipcode = value_for('lab.zipcode', server_data)
    lab_full_address = str(lab_address_1) + ' ' + str(lab_address_2) + ', ' + str(lab_city) + ', ' + str(lab_state) + ' ' + str(lab_zipcode)
    print "Formatting Lab Address..."
    server_data = set_value('lab.full_address', lab_full_address, server_data)
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

    print "Formatting Category/Type/Production..."
    server_data = set_value('category_type_production', category_type_production, server_data)

    initial_weight = value_for('initial_weight', server_data)
    batch_info = 'Batch #: ' + '' + '; Batch Size: ' + str(initial_weight) + ' - grams'
    print "Formatting Batch Info..."
    server_data = set_value('batch_info', batch_info, server_data)
    initial_weight = str(initial_weight) + ' grams'
    print "Formatting Initial Weight..."
    server_data = set_value('initial_weight', initial_weight, server_data)
    date_received = value_for('date_received', server_data)
    if date_received is None or date_received == 'null' or date_received == '':
        date_received = ''
    else:
        date_received = date_received.split(',')[1].split(' ')
        date_received = date_received[:-2]
        date_received = months[date_received[2]] + '/' + date_received[1] + '/' + date_received[3]
    last_modified = value_for('last_modified', server_data)
    if last_modified is None or last_modified == 'null' or last_modified == '':
        last_modified = ''
    else:
        last_modified = last_modified.split(',')[1].split(' ')
        last_modified = last_modified[:-2]
        last_modified = months[last_modified[2]] + '/' + last_modified[1] + '/' + last_modified[3]
    date_completed = value_for('date_completed', server_data)
    if date_completed is None or date_completed == 'null' or date_completed == '':
        date_completed = ''
        expires = ''
    else:
        complete_split = date_completed.split('/')
        year = complete_split[2]
        year2 = int(year) + 1
        year3 = str(year2)
        expires = str(complete_split[0]) + '/' + str(complete_split[1]) + '/' + year3

    if str(date_completed) == '':
        bunch_of_dates = 'Ordered: ' + str(date_received) + '; Sampled: ' + str(last_modified)
    else:
        bunch_of_dates = 'Ordered: ' + str(date_received) + '; Sampled: ' + str(last_modified) + '; Completed: ' + str(date_completed) + '; Expires: ' + str(expires)
    print "Formatting Bunch of Dates..."
    server_data = set_value('bunch_of_dates', bunch_of_dates, server_data)

    type_and_method = str(value_for('type.name', server_data)) + ', ' + str(value_for('method.name', server_data))
    print "Formatting Type/Method..."
    server_data = set_value('type_and_method', type_and_method, server_data)

    lab_full_street_address = str(value_for('lab.address_line_1', server_data)) + ' ' + str(value_for('lab.address_line_2', server_data))
    print "Formatting Lab Street Address..."
    server_data = set_value('lab.full_street_address', lab_full_street_address, server_data)
    lab_city_state_zip = str(value_for('lab.city', server_data).title()) + ', ' + str(value_for('lab.state', server_data)) + ' ' + str(value_for('lab.zipcode', server_data))
    print "Formatting Lab City/State/Zip..."
    server_data = set_value('lab.city_state_zip', lab_city_state_zip, server_data)
    client_city_state_zip = str(value_for('client_info.city', server_data).title()) + ', ' + str(value_for('client_info.state', server_data)) + ' ' + str(value_for('client_info.zipcode', server_data))
    print "Formatting Client City/State/Zip..."
    server_data = set_value('client.city_state_zip', client_city_state_zip, server_data)
    server_data = set_value('special', {}, server_data)
    print "Formatting Date Received..."
    server_data = set_value('date_received', date_received, server_data)
    print "Formatting Last Modified..."
    server_data = set_value('last_modified', last_modified, server_data)
    # try:
    #     metric_lot_number = value_for('additional_info.metric_lot_number', server_data, default='')
    #     metric_manifest_number = value_for('additional_info.metric_manifest_number', server_data, default='')
    #     metric_package_number = value_for('additional_info.metric_package_number', server_data, default='')
    #
    #     metric_info = "METRC Lot #: " + str(metric_lot_number) + '; METRC Manifest #: ' + metric_manifest_number + '; METRC Package Tag #: ' + metric_package_number
    # except Exception as e:
    #     print "------------------------------------------"
    #     print bcolors.FAIL + "Metric Fields Exception" + bcolors.ENDC
    #     print str(e)
    #     print "------------------------------------------"
    #     pass

    # server_data = set_value('metric_info', metric_info, server_data)
    r_units = value_for('lab_data.cannabinoids.report_units', server_data)
    client_license_number = 'Lic. # ' + str(value_for('client_license.license_number', server_data))
    print "Formatting Client License Number..."
    server_data = set_value('client_license.license_number', client_license_number, server_data)
    digits = value_for('lab_data.cannabinoids.digits', server_data)
    special_total_cannabinoids = get_total_cannabinoids([value_for('lab_data.cannabinoids.tests', server_data), value_for('lab_data.thc.tests', server_data)], r_units, digits, display=True)
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

    print "THC Total..."
    print special_thc_total
    print "CBD Total..."
    print special_cbd_total
    non_decimal = re.compile(r'[^\d.]+')
    new_special_thc_total = non_decimal.sub('', special_thc_total)
    new_special_cbd_total = non_decimal.sub('', special_cbd_total)
    # print new_special_thc_total
    # print new_special_cbd_total
    if make_number(new_special_thc_total) == 0 or make_number(new_special_cbd_total) == 0:
        thc_ratio = ''
        cbd_ratio = ''
    else:
        if make_number(new_special_thc_total) > make_number(new_special_cbd_total):
            thc_ratio = make_number(make_number(new_special_thc_total)/make_number(new_special_cbd_total), digits=1, labels=True)
            cbd_ratio = 1.0
        else:
            thc_ratio = 1.0
            cbd_ratio = make_number(make_number(new_special_cbd_total)/make_number(new_special_thc_total), digits=1, labels=True)

    special = {
        'total_thc': str(special_thc_total),
        'total_cbd': str(special_cbd_total),
        'moisture': str(special_moisture),
        'total_cannabinoids': str(special_total_cannabinoids),
        'water_activity': str(make_number(value_for('lab_data.water_activity.tests.aw.value', server_data), wa_digits, labels=True)),
        'thc_ratio': str(thc_ratio),
        'cbd_ratio': str(cbd_ratio)
    }

    status_map = {
        '-1': 'Not Tested',
        '0': 'In Progress',
        '1': 'Pass',
        '2': 'Fail',
        '3': 'Complete'
        }

    status_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals', 'thc', 'foreign_matter', 'moisture']
    for category in status_categories:
        status_value = str(value_for('lab_data.' + category + '.status', server_data))
        print "Formatting " + category.title() + " Status Message..."
        server_data = set_value('lab_data.' + category + '.status', str(value_for(status_value, status_map)), server_data)
    print "Formatting Special Fields (Total THC, Total CBD, Moisture, Total Cannabinoids, Water Activity)..."
    server_data = set_value('special', special, server_data)
    print bcolors.BOLD
    print "--------------------------------------"
    print "Beginning Category Data Modifications"
    print "--------------------------------------"
    print bcolors.ENDC
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

            if category == 'cannabinoids':
                print "Setting up Visualizaiton Data..."
                report_columns = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="secondary_report_units"></i></span>', 'width': '25%'}]
                report_columns2 = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': ' ', 'className': 'right', 'width': '75%'}]
                report_columns3 = [{'title': 'Analyte', 'className': 'left', 'width': '20%'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="secondary_report_units"></i></span>', 'width': '20%'}, {'title': ' ', 'className': 'right', 'width': '20%'}];
                server_data = set_value(category + '_report_columns3', report_columns3, server_data)
                server_data = set_value(category + '_report_columns2', report_columns2, server_data)
                server_data = set_value(category + '_report_columns', report_columns, server_data)

                cbd_data = value_for('lab_data.cannabinoids.tests', server_data)
                thc_data = value_for('lab_data.thc.tests', server_data)
                print "Setting up Ordered Data..."
                ordered = high_to_low([cbd_data, thc_data], report_units)
                # print "ordered:"
                # print ordered
                ordered_and_numbered = numberize(ordered, category)
                # print "ordered_and_numbered:"
                # print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)
                # print "server_data[category + '_ordered']:"
                # print value_for(category + '_ordered', server_data)
                cannabinoid_data = value_for('lab_data.cannabinoids.tests', server_data)
                # print "cannabinoid_data"
                # print cannabinoid_data
                total_cannabinoid_concentration = get_concentration_total([cannabinoid_data, thc_data], str(report_units))
                # print "total_cannabinoid_concentration"
                # print total_cannabinoid_concentration
                # print "report_units"
                # print report_units
                print "Finding Analyte with Highest Concentration..."
                highest = get_winner([cannabinoid_data, thc_data], str(report_units))
                print "Preparing Datatable Data..."
                combined_cannabinoids_dt = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)
                print "Adding Totals to Datatable Data..."

                add_cannabinoid_totals(combined_cannabinoids_dt, report_units, secondary_report_units, digits)
                add_units_to_tables(combined_cannabinoids_dt, report_columns, report_units, secondary_report_units)
                # print "combined cannabinoid dt"
                print "Preparing Sparkline Data..."
                combined_cannabinoids_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)

                combined_cannabinoids_sl = format_sparkline_data(combined_cannabinoids_sl)

                # print "combined cannabinoid sl"
                print "Preparing Datatable/Sparkline Data..."
                combined_cannabinoids_dt_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)

                data_list = [cannabinoid_data, thc_data]
                num_of_items = sum(len(x.keys()) for x in data_list)
                color_list = []
                if num_of_items > 0:
                    color_list = get_colors(num_of_items)
                print "Preparing Pietable Data..."
                combined_category_pie = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'pietable', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                print "Preparing Piechart Data..."
                combined_category_pie2 = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'piechart', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                if len(combined_category_pie2) > 0:
                    if len(combined_category_pie2[0]) > 0:
                        combined_category_pie2.sort(key=lambda x: make_number(x[1]), reverse=True)
                        combined_category_pie2.insert(0, ['Cannabinoid', 'Concentration'])
                        color_list = resort_colors(color_list, combined_category_pie, combined_category_pie2)
                print "Adding Totals to Datatable/Sparkline..."
                add_cannabinoid_totals(combined_cannabinoids_dt_sl, report_units, secondary_report_units, digits, combined=True)
                add_units_to_tables(combined_cannabinoids_dt_sl, report_columns, report_units, secondary_report_units)
                viztypes['datatable_cannabinoids'] = combined_cannabinoids_dt
                viztypes['sparkline_cannabinoids'] = combined_cannabinoids_sl
                viztypes['datatable_cannabinoids_with_sparkline'] = combined_cannabinoids_dt_sl
                viztypes['pietable_cannabinoids'] = combined_category_pie
                viztypes['piechart_cannabinoids'] = combined_category_pie2
                viztypes['colors_cannabinoids'] = color_list
                update_color_list(color_list, 'cannabinoids_colors.js')
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
                # server_data['category_units'][category] = [
                #     ru,
                #     sru
                # ]
                server_data = set_value('category_units.' + category, [ru, sru], server_data)
                # print "cannabinoid_data again:"
                # print cannabinoid_data
                print "Adding Units to Analyte Values"
                new_test_data = add_units_to_values(cannabinoid_data)
                # print "made it to right after adding units"
                server_data = set_value('lab_data.cannabinoids.tests', new_test_data, server_data)
            elif category == 'microbials':
                print "Setting up Visualizaiton Data..."
                report_columns = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': 'Limit<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Status<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;"></i></span>', 'width': '25%'}]
                report_columns2 = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': ' ', 'className': 'right', 'width': '75%'}]
                report_columns3 = [{'className': 'left', 'width': '20%', 'title': 'Analyte'}, {'width': '20%', 'title': 'Limit<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>'}, {'width': '20%', 'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>'}, {'width': '20%', 'title': 'Status<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;"></i></span>'}, {'title': ' ', 'className': 'right', 'width': '20%'}];
                server_data = set_value(category + '_report_columns3', report_columns3, server_data)
                server_data = set_value(category + '_report_columns2', report_columns2, server_data)

                server_data = set_value(category + '_report_columns', report_columns, server_data)
                # print "----------------------------------------------------------------"
                # print value_for('lab_data.' + category, server_data)
                # print "----------------------------------------------------------------"
                category_data = value_for('lab_data.' + category + '.tests', server_data, default={})
                print "Setting up Ordered Data..."
                ordered = high_to_low([category_data], report_units)
                # print "ordered:"
                # print ordered
                ordered_and_numbered = numberize(ordered, category)
                # print "ordered_and_numbered:"
                # print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)

                # print "server_data[category + '_ordered']:"
                # print value_for(category + '_ordered', server_data)
                # print "yay for category data"

                total_category_concentration = get_concentration_total([category_data], str(report_units))
                # print "yay for total_category_concentration"
                print "Finding Analyte with Highest Concentration..."
                highest = get_winner([category_data], str(report_units))
                # print "made it past get_winner"
                print "Preparing Datatable Data..."
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)
                # print category_dt
                if len(category_dt) > 0:
                    if len(category_dt[0]) > 0:
                        category_dt.sort(key=lambda x: x[0])
                # print "yay for category dt"
                add_units_to_tables(category_dt, report_columns, report_units, secondary_report_units)
                print "Preparing Sparkline Data..."
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest
                )
                category_sl = format_sparkline_data(category_sl)
                # print category_sl
                print "Preparing Datatable/Sparkline Data..."
                combined_category_dt_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                # print combined_category_dt_sl
                data_list = [category_data]
                # print "data_list:"
                # print data_list
                # print "num_of_items:"
                add_units_to_tables(combined_category_dt_sl, report_columns, report_units, secondary_report_units)
                num_of_items = sum(len(x.keys()) for x in data_list)
                # print num_of_items
                color_list = []
                if num_of_items > 0:
                    color_list = get_colors(num_of_items)
                print "Preparing Pietable Data..."
                combined_category_pie = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'pietable', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                # print "pietable:"
                # print combined_category_pie
                viztypes['datatable_' + category + '_with_sparkline'] = combined_category_dt_sl
                print "Preparing Piechart Data..."
                combined_category_pie2 = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'piechart', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                # print "piechart:"
                # print combined_category_pie2
                if len(combined_category_pie2) > 0:
                    if len(combined_category_pie2[0]) > 0:
                        combined_category_pie.sort(key=lambda x: make_number(x[0]))
                        combined_category_pie2.sort(key=lambda x: make_number(x[1]), reverse=True)
                        combined_category_pie2.insert(0, ['Microbial', 'Concentration'])
                        color_list = resort_colors(color_list, combined_category_pie, combined_category_pie2)
                # print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                viztypes['pietable_' + category] = combined_category_pie
                viztypes['pichart_' + category] = combined_category_pie2
                viztypes['colors_' + category] = color_list
                update_color_list(color_list, category + '_colors.js')
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
                # server_data['category_units'][category] = [
                #     ru,
                #     sru
                # ]
                server_data = set_value('category_units.' + category, [ru, sru], server_data)
                # cat_cat_units = [
                #     report_units,
                #     secondary_report_units
                # ]
                # server_data = set_value('category_units.' + category, cat_cat_units, server_data)
                print "Adding Units to Analyte Values..."
                new_test_data = add_units_to_values(category_data)
                server_data = set_value('lab_data.' + category + '.tests', new_test_data, server_data)
            else:
                print "Setting up Visualizaiton Data..."
                report_columns = [{'title': 'Analyte', 'className': 'left', 'width': '20%'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'},  {'title': 'Limit<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Status<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;"></i></span>', 'width': '20%'}]
                category_data = value_for('lab_data.' + category + '.tests', server_data, default={})
                report_columns2 = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': ' ', 'className': 'right', 'width': '75%'}]
                server_data = set_value(category + '_report_columns2', report_columns2, server_data)
                report_columns3 = [{'className': 'left', 'width': '20%', 'title': 'Analyte'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'},  {'width': '20%', 'title': 'Limit<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>'}, {'width': '20%', 'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>'}, {'width': '20%', 'title': 'Status<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;"></i></span>'}, {'title': ' ', 'className': 'right', 'width': '20%'}];
                # server_data = set_value(category + '_report_columns3', report_columns3, server_data)
                # print "yay for category data"
                print "Setting up Ordered Data..."
                # print category_data
                ordered = high_to_low([category_data], report_units)
                # print ordered
                # print "ordered:"
                # print ordered
                # print "Ordering and Numerization..."
                ordered_and_numbered = numberize(ordered, category)
                # print "ordered_and_numbered:"
                # print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)
                # print "server_data[category + '_ordered']:"
                # print value_for(category + '_ordered', server_data)
                # print "Finding Total Concentration..."
                total_category_concentration = get_concentration_total([category_data], str(report_units))
                # print "yay for total_category_concentration"
                print "Finding Analyte with Highest Concentration..."
                highest = get_winner([category_data], str(report_units))
                print "Preparing Datatable Data..."
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)

                # print "yay for category dt"
                print "Preparing Sparkline Data..."
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest
                )
                category_sl = format_sparkline_data(category_sl)
                data_list = [category_data]
                num_of_items = sum(len(x.keys()) for x in data_list)
                color_list = []
                if num_of_items > 0:
                    color_list = get_colors(num_of_items)
                print "Preparing Pietable Data..."
                combined_category_pie = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'pietable', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                print "Preparing Piechart Data..."
                combined_category_pie2 = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'piechart', digits, report_units, secondary_report_units,
                    total_concentration=highest, color_list=color_list)
                if category == 'terpenes':
                    report_columns = [{'title': 'Analyte', 'className': 'left', 'width': '25%'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '25%'}]
                    report_columns3 = [{'title': 'Analyte', 'className': 'left', 'width': '20%'}, {'title': 'LOQ<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': 'Mass<span><i style="font-size: 7px;position: relative;margin-left: 7px;color: #808080;" class="report_units"></i></span>', 'width': '20%'}, {'title': ' ', 'className': 'right', 'width': '20%'}]
                    if len(combined_category_pie2) > 0:
                        if len(combined_category_pie2[0]) > 0:
                            combined_category_pie2.sort(key=lambda x: make_number(x[1]), reverse=True)
                            combined_category_pie2.insert(0, ['Terpene', 'Concentration'])
                            combined_category_pie.sort(key=lambda x: make_number(x[1]), reverse=True)
                            color_list = resort_colors(color_list, combined_category_pie, combined_category_pie2)
                    if len(category_dt) > 0:
                        if len(category_dt[0]) > 0:
                            category_dt.sort(key=lambda x: make_number(x[2]), reverse=True)
                    if len(category_sl) > 0:
                        if len(category_sl[0]) > 0:
                            category_sl.sort(key=lambda x: make_number(x[1]), reverse=True)

                else:
                    if len(category_dt) > 0:
                        if len(category_dt[0]) > 0:
                            category_dt.sort(key=lambda x: x[0])
                    if len(category_sl) > 0:
                        if len(category_sl[0]) > 0:
                            category_sl.sort(key=lambda x: x[0])
                    if len(combined_category_pie2) > 0:
                        if len(combined_category_pie2[0]) > 0:
                            combined_category_pie.sort(key=lambda x: x[0])
                            combined_category_pie2.sort(key=lambda x: make_number(x[1]), reverse=True)
                            combined_category_pie2.insert(0, [category[:-1], 'Concentration'])
                            color_list = resort_colors(color_list, combined_category_pie, combined_category_pie2)
                server_data = set_value(category + '_report_columns', report_columns, server_data)
                server_data = set_value(category + '_report_columns3', report_columns3, server_data)
                # print "yay for category sl"
                print "Preparing Datatable/Sparkline Data..."
                combined_category_dt_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                add_units_to_tables(category_dt, report_columns, report_units, secondary_report_units)
                add_units_to_tables(combined_category_dt_sl, report_columns, report_units, secondary_report_units)
                viztypes['datatable_' + category + '_with_sparkline'] = combined_category_dt_sl
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                viztypes['pietable_' + category] = combined_category_pie
                viztypes['piechart_' + category] = combined_category_pie2
                viztypes['colors_' + category] = color_list
                update_color_list(color_list, category + '_colors.js')
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
                # server_data['category_units'][category] = [
                #     ru,
                #     sru
                # ]
                server_data = set_value('category_units.' + category, [ru, sru], server_data)
                # cat_cat_units = [
                #     report_units,
                #     secondary_report_units
                # ]
                # server_data = set_value('category_units.' + category, cat_cat_units, server_data)
                print "Adding Units to Analyte Values..."
                new_test_data = add_units_to_values(category_data)
                server_data = set_value('lab_data.' + category + '.tests', new_test_data, server_data)
        except Exception as e:
            print "------------------------------------------"
            print bcolors.FAIL + "COA Job Exception" + bcolors.ENDC
            print str(e)
            print "------------------------------------------"
            continue


    thc_data = value_for('lab_data.thc.tests', server_data)
    new_test_data = add_units_to_values(thc_data)
    server_data = set_value('lab_data.thc.tests', new_test_data, server_data)
    server_data = set_value('lab_data_latest', value_for('lab_data', server_data), server_data)
    server_data = set_value('viz', viztypes, server_data)

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
            os.path.join('coa', template_folder),
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
    print "Test Packages Found:"
    print value_for('test_packages', server_data)
    template_keys = get_test_packages(value_for('test_packages', server_data))
    print "Finding Templates for the Test Packages..."
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    # print "--------------------------------------"
    if len(templates) < 1:
        print "No Matching Templates Found..."
        response = {
            'status': 'PDF Generation Terminated!',
            'error': 'No templates were found to be used with this data.'
        }
        return response
    print "Matched Templates:"
    templates = list(set(templates))
    templates.sort()
    print templates
    # print "--------------------------------------"
    print "Retrieving Logo..."
    lab_logo = s3templates.get_logo('/tmp/work/config.yaml')
    server_data['lab_logo'] = lab_logo
    print "Finding Special Scripts..."
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "Downloading Matched Templates..."
        # print str(templates)
        s3templates.download_templates(os.path.join('coa', template_folder), templates)
        print "Downloading Special Scripts..."
        s3templates.download_scripts(os.path.join('coa', template_folder), scripts)
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
    print "Finished Preparing Data for COA"
    print "--------------------------------------"
    print bcolors.ENDC
    # print str(data)
    return response
