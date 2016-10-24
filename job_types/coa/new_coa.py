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
from collections import OrderedDict
from operator import itemgetter
import yaml
from decimal import Decimal


def value_for(endpoint, data, default='', encoding=None):
    points = endpoint.split('.')
    value = ''
    for i, e in enumerate(points):
        if e in data:
            data = data[e]
            value = data
        else:
            value = default
            break
    if encoding is not None:
        value = value.encode(encoding)
    return value

def set_value(endpoint, value, data):
    points = endpoint.split('.')
    current_data = data
    if len(points) < 2:
        current_data[points[0]] = value
    else:
        for i, e in enumerate(points):
            if e not in current_data or not isinstance(current_data[e], collections.Mapping):
                current_data[e] = {}
            slicer = (i + 1)
            sliced_points = points[slicer:]
            new_endpoint = '.'.join(sliced_points)
            set_value(new_endpoint, value, current_data[e])

    return current_data

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
        data = float(data)
    except ValueError:
        if data == "<LOQ":
            data = "&ltLOQ"
        if not labels:
            data = float(0)

    output = data
    if digits is not None and isinstance(data, float):
        dec = Decimal(data)
        output = round(dec, int(digits))
    return output

def get_winner(data_list, display_value):
    highest = 0.0
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                try:
                    value = make_number(data[analyte]['display'][display_value]['value'])
                    if value > highest:
                        highest = value
                except Exception as e:
                    print str(e)
                    print "get_winner exception"
                    continue
    return highest

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

def add_units_to_values(tests):
    formatted_tests = tests
    for analyte in tests:
        print analyte
        for display_chunk in tests[analyte]['display']:
            print display_chunk
            if display_chunk not in ['name', 'aroma']:
                for value_type in tests[analyte]['display'][display_chunk]:
                    print value_type
                    try:
                        converted_value = float(str(tests[analyte]['display'][display_chunk][value_type]))
                        dec = Decimal(converted_value).quantize(Decimal(10) ** -2)
                        # dec = Decimal(converted_value)
                        output = dec
                        if str(display_chunk) in ['ppm', 'ppb', 'cfu/g']:
                            output = int(round(dec, 0))
                        new_display_chunk = display_chunk
                        if str(display_chunk) != '%':
                            if str(display_chunk) in ['ppm','ppb']:
                                new_display_chunk = ' ' + str(display_chunk).upper()
                            if str(display_chunk) == 'cfu/g':
                                new_display_chunk = ' CFU/g'
                            if str(display_chunk) == 'mg/ml':
                                new_display_chunk = ' mg/mL'
                        units = str(new_display_chunk)
                        formatted_tests[analyte]['display'][display_chunk][value_type] = str(output) + str(units)
                    except Exception as e:
                        print str(e)
                        print "made it to the add_units exception"
                        converted_value = str(tests[analyte]['display'][display_chunk][value_type])
                        formatted_tests[analyte]['display'][display_chunk][value_type] = str(converted_value)
                        print "converterd to: " + str(formatted_tests[analyte]['display'][display_chunk][value_type])
                        continue

    return formatted_tests




def combine_tests_for_viz(data_list, category, viz_type, digits, display_unit='%', display_unit2='mg/g', total_concentration=None):
    combined_list = []
    special_list = []
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                if viz_type == 'datatable_sparkline':
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
                                make_number(data[analyte]['display'][display_unit]['limit'], digits, labels=True),
                                make_number(data[analyte]['display'][display_unit]['value'], digits, labels=True),
                                status,
                                '<progress max="' + str(make_number(total_concentration, digits)) + '" value="' + str(make_number(data[analyte]['display'][display_unit]['value'], digits)) + '"></progress>'
                            ]
                        )
                        # make_number(data[analyte]['display'][display_unit]['value'], digits),
                        # make_number(total_concentration, digits)
                    else:
                        report_data = [
                            str(data[analyte]['display']['name']),
                            make_number(data[analyte]['display'][display_unit]['loq'], digits, labels=True),
                            make_number(data[analyte]['display'][display_unit]['value'], digits, labels=True),
                            make_number(data[analyte]['display'][display_unit2]['value'], digits, labels=True),
                            '<progress max="' + str(make_number(total_concentration, digits)) + '" value="' + str(make_number(data[analyte]['display'][display_unit]['value'], digits)) + '"></progress>'
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
                                make_number(data[analyte]['display'][display_unit]['limit'], digits, labels=True),
                                make_number(data[analyte]['display'][display_unit]['value'], digits, labels=True),
                                status
                            ]
                        )
                    else:
                        report_data = [
                            str(data[analyte]['display']['name']),
                            make_number(data[analyte]['display'][display_unit]['loq'], digits, labels=True),
                            make_number(data[analyte]['display'][display_unit]['value'], digits, labels=True),
                            make_number(data[analyte]['display'][display_unit2]['value'], digits, labels=True)
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
                        str(data[analyte]['display']['name']),
                        make_number(data[analyte]['display'][display_unit]['value'], digits),
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
    return combined_list

def add_cannabinoid_totals(combined_list, display_unit, display_unit2, digits, combined=False):
    primary_total = 0.0
    secondary_total = 0.0
    for row in combined_list:
        primary = make_number(row[2])
        secondary = make_number(row[3])
        primary_total += primary
        secondary_total += secondary

    primary_total = str(primary_total)
    secondary_total = str(secondary_total)
    # if display_unit == '%':
    #     primary_total = str(primary_total) + '%'
    # if display_unit2 == '%':
    #     secondary_total = str(secondary_total) + '%'
    if combined:
        combined_list.append(
            [
                'Total Cannabinoids',
                '',
                primary_total,
                secondary_total,
                ''
            ]
        )

    else:
        combined_list.append(
            [
                'Total Cannabinoids',
                '',
                primary_total,
                secondary_total
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
    server_data = set_value('qr_code', qr_base + public_profile_base + public_key, server_data)
    template_folder = value_for('lab.abbreviation', server_data)
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
    server_data = set_value('formatted_client_phone', formatted_phone(client_phone), server_data)
    lab_phone = value_for('lab.phone', server_data)
    server_data = set_value('formatted_lab_phone', formatted_phone(lab_phone), server_data)
    client_address_1 = value_for('client_info.address_line_1', server_data)
    client_address_2 = value_for('client_info.address_line_2', server_data)
    client_city = value_for('client_info.city', server_data)
    client_state = value_for('client_info.state', server_data)
    client_zipcode = value_for('client_info.zipcode', server_data)
    client_full_address = str(client_address_1) + ' ' + str(client_address_2) + ', ' + str(client_city) + ', ' + str(client_state) + ' ' + str(client_zipcode)
    server_data = set_value('client.full_address', client_full_address, server_data)
    lab_address_1 = value_for('lab.address_line_1', server_data)
    lab_address_2 = value_for('lab.address_line_2', server_data)
    lab_city = value_for('lab.city', server_data)
    lab_state = value_for('lab.state', server_data)
    lab_zipcode = value_for('lab.zipcode', server_data)
    lab_full_address = str(lab_address_1) + ' ' + str(lab_address_2) + ', ' + str(lab_city) + ', ' + str(lab_state) + ' ' + str(lab_zipcode)
    server_data = set_value('lab.full_address', lab_full_address, server_data)

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

    server_data = set_value('category_type_production', category_type_production, server_data)

    initial_weight = value_for('initial_weight', server_data)
    batch_info = 'Batch #: ' + '' + '; Batch Size: ' + str(initial_weight) + ' - grams'
    server_data = set_value('batch_info', batch_info, server_data)
    initial_weight = str(initial_weight) + ' grams'
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
    server_data = set_value('bunch_of_dates', bunch_of_dates, server_data)

    type_and_method = str(value_for('type.name', server_data)) + ', ' + str(value_for('method.name', server_data))
    server_data = set_value('type_and_method', type_and_method, server_data)

    lab_full_street_address = str(value_for('lab.address_line_1', server_data)) + ' ' + str(value_for('lab.address_line_2', server_data))
    server_data = set_value('lab.full_street_address', lab_full_street_address, server_data)
    lab_city_state_zip = str(value_for('lab.city', server_data).title()) + ', ' + str(value_for('lab.state', server_data)) + ' ' + str(value_for('lab.zipcode', server_data))
    server_data = set_value('lab.city_state_zip', lab_city_state_zip, server_data)
    client_city_state_zip = str(value_for('client_info.city', server_data).title()) + ', ' + str(value_for('client_info.state', server_data)) + ' ' + str(value_for('client_info.zipcode', server_data))
    server_data = set_value('client.city_state_zip', client_city_state_zip, server_data)
    server_data = set_value('special', {}, server_data)
    server_data = set_value('date_received', date_received, server_data)
    server_data = set_value('last_modified', last_modified, server_data)

    r_units = value_for('lab_data.cannabinoids.report_units', server_data)
    client_license_number = 'Lic. # ' + str(value_for('client_license.license_number', server_data))
    server_data = set_value('client_license.license_number', client_license_number, server_data)

    special_cbd_total = str(value_for('lab_data.cannabinoids.cbd_total.display.' + str(r_units) + '.value', server_data))

    if special_cbd_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
        special_cbd_total = round(float(special_cbd_total), 1)
        special_cbd_total = str(special_cbd_total)
        special_cbd_total = special_cbd_total + str(r_units)
    special_thc_total = str(value_for('lab_data.thc.thc_total.display.' + r_units + '.value', server_data))
    if special_thc_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
        special_thc_total = round(float(special_thc_total), 1)
        special_thc_total = str(special_thc_total)
        special_thc_total = special_thc_total + str(r_units)


    special_moisture = str(value_for('lab_data.moisture.tests.percent_moisture.display.%.value', server_data))
    if str(special_moisture) != '' and str(special_moisture) not in ['ND', 'NR']:
        special_moisture = round(float(special_moisture), 1)
        special_moisture = str(special_moisture)
        special_moisture = str(special_moisture) + '%'


    new_unit = str(r_units)
    if r_units != '%':
        new_unit = ' ' + r_units


    special = {
        'total_thc': str(special_thc_total),
        'total_cbd': str(special_cbd_total),
        'moisture': str(special_moisture)
    }

    server_data = set_value('special', special, server_data)

    for category in test_categories:
        print "we're on category ------------------->  " + category
        try:
            digits = value_for('lab_data.' + category + '.digits', server_data)
            report_units = value_for('lab_data.' + category + '.report_units', server_data)
            secondary_report_units = 'mg/g'
            if report_units == 'mg/g':
                secondary_report_units = '%'
            if report_units == '%':
                secondary_report_units = 'mg/g'

            if category == 'cannabinoids':
                cbd_data = value_for('lab_data.cannabinoids.tests', server_data)
                thc_data = value_for('lab_data.thc.tests', server_data)

                ordered = high_to_low([cbd_data, thc_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)
                print "server_data[category + '_ordered']:"
                print value_for(category + '_ordered', server_data)
                cannabinoid_data = value_for('lab_data.cannabinoids.tests', server_data)
                print "cannabinoid_data"
                print cannabinoid_data
                total_cannabinoid_concentration = get_concentration_total([cannabinoid_data, thc_data], str(report_units))
                print "total_cannabinoid_concentration"
                print total_cannabinoid_concentration
                print "report_units"
                print report_units
                highest = get_winner([cannabinoid_data, thc_data], str(report_units))
                combined_cannabinoids_dt = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)

                add_cannabinoid_totals(combined_cannabinoids_dt, report_units, secondary_report_units, digits)
                print "combined cannabinoid dt"
                combined_cannabinoids_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                print "combined cannabinoid sl"
                combined_cannabinoids_dt_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                add_cannabinoid_totals(combined_cannabinoids_dt_sl, report_units, secondary_report_units, digits, combined=True)
                viztypes['datatable_cannabinoids'] = combined_cannabinoids_dt
                viztypes['sparkline_cannabinoids'] = combined_cannabinoids_sl
                viztypes['datatable_cannabinoids_with_sparkline'] = combined_cannabinoids_dt_sl
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
                server_data['category_units'][category] = [
                    ru,
                    sru
                ]
                print "cannabinoid_data again:"
                print cannabinoid_data
                new_test_data = add_units_to_values(cannabinoid_data)
                server_data = set_value('lab_data.cannabinoids.tests', new_test_data, server_data)
            elif category == 'microbials':
                print "----------------------------------------------------------------"
                print value_for('lab_data.' + category, server_data)
                print "----------------------------------------------------------------"
                category_data = value_for('lab_data.' + category + '.tests', server_data)
                ordered = high_to_low([category_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)

                print "server_data[category + '_ordered']:"
                print value_for(category + '_ordered', server_data)
                print "yay for category data"
                total_category_concentration = get_concentration_total([category_data], str(report_units))
                print "yay for total_category_concentration"
                highest = get_winner([category_data], str(report_units))
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)
                category_dt.sort(key=lambda x: x[0])
                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest
                )
                combined_category_dt_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                viztypes['datatable_' + category + '_with_sparkline'] = combined_category_dt_sl
                print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                cat_cat_units = [
                    report_units,
                    secondary_report_units
                ]
                server_data = set_value('category_units.' + category, cat_cat_units, server_data)
                new_test_data = add_units_to_values(category_data)
                server_data = set_value('lab_data.' + category + '.tests', new_test_data, server_data)
            else:
                category_data = value_for('lab_data.' + category + '.tests', server_data)


                print "yay for category data"
                ordered = high_to_low([category_data], report_units)
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered, category)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data = set_value(category + '_ordered', ordered_and_numbered, server_data)
                print "server_data[category + '_ordered']:"
                print value_for(category + '_ordered', server_data)
                total_category_concentration = get_concentration_total([category_data], str(report_units))
                print "yay for total_category_concentration"
                highest = get_winner([category_data], str(report_units))
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable', digits, report_units, secondary_report_units)

                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest
                )
                if category == 'terpenes':
                    category_dt.sort(key=lambda x: x[2], reverse=True)
                    category_sl.sort(key=lambda x: x[1], reverse=True)
                else:
                    category_dt.sort(key=lambda x: x[0], reverse=True)
                    category_sl.sort(key=lambda x: x[0], reverse=True)
                print "yay for category sl"
                combined_category_dt_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    category, 'datatable_sparkline', digits, report_units, secondary_report_units,
                    total_concentration=highest)
                viztypes['datatable_' + category + '_with_sparkline'] = combined_category_dt_sl
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
                cat_cat_units = [
                    report_units,
                    secondary_report_units
                ]
                server_data = set_value('category_units.' + category, cat_cat_units, server_data)
                new_test_data = add_units_to_values(category_data)
                server_data = set_value('lab_data.' + category + '.tests', new_test_data, server_data)
        except Exception as e:
            print "made it to the coa exception"
            print str(e)
            continue


    thc_data = value_for('lab_data.thc.tests', server_data)
    new_test_data = add_units_to_values(thc_data)
    server_data = set_value('lab_data.thc.tests', new_test_data, server_data)
    server_data = set_value('lab_data_latest', value_for('lab_data', server_data), server_data)
    server_data = set_value('viz', viztypes, server_data)

    print "Initializing S3TemplateService"

    if os.path.exists('/tmp/work'):
        shutil.rmtree('/tmp/work')
    if not os.path.exists('/tmp/work'):
        os.makedirs('/tmp/work')

    if 'run_local' in server_data:
        print "Initializing TemplateService"
        s3templates = TemplateService(server_data['run_local'])
    else:
        print "Initializing S3TemplateService"
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
    print "test_packages:"
    print value_for('test_packages', server_data)
    template_keys = get_test_packages(value_for('test_packages', server_data))
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    templates = list(set(templates))
    templates.sort()
    lab_logo = s3templates.get_logo('/tmp/work/config.yaml')
    server_data['lab_logo'] = lab_logo
    print "getting scripts"
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "downloading templates"
        print str(templates)
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
        response = job.run(data, templates, s3templates)
        data = response['data']
        templates = response['templates']
    response = {
        'templates': templates,
        'data': data
    }
    print "these are the templates: "
    print str(templates)
    print "made it to the end of this section......................................."
    print str(data)
    return response
