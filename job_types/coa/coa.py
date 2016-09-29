# -*- coding: utf-8 -*
# python 2

import sys
import imp
import os
sys.path.append('../..')
import time
import shutil
from pdfservices import S3TemplateService
from collections import OrderedDict
from operator import itemgetter
import yaml
from decimal import Decimal

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
    lab_slug = server_data['lab']['slug']
    public_profile_base = 'https%3A%2F%2Forders.confidentcannabis.com%2F' + str(lab_slug) + '%2F%23!%2Freport%2Fpublic%2Fsample%2F'
    public_key = server_data['public_key']
    server_data['qr_code'] = qr_base + public_profile_base + public_key
    template_folder = server_data['lab']['abbreviation']
    test_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals']
    server_data['category_units'] = {}
    try:
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
        server_data['formatted_client_phone'] = formatted_phone(server_data['client_info']['phone'])
        server_data['formatted_lab_phone'] = formatted_phone(server_data['lab']['phone'])
        server_data['client']['full_address'] = str(server_data['client_info']['address_line_1']) + ' ' + str(server_data['client_info']['address_line_2']) + ', ' + str(server_data['client_info']['city']) + ', ' + str(server_data['client_info']['state']) + ' ' + str(server_data['client_info']['zipcode'])
        server_data['lab']['full_address'] = str(server_data['lab']['address_line_1']) + ' ' + str(server_data['lab']['address_line_2']) + ', ' + str(server_data['lab']['city']) + ', ' + str(server_data['lab']['state']) + ' ' + str(server_data['lab']['zipcode'])
        ## dd/mm/yyyy format
        server_data['date_completed'] = str(time.strftime("%m/%d/%Y"))
        date_completed = server_data['date_completed']
        # server_data['lab']['license'] = server_data['lab_license']
        #server_data['page_of_pages'] = ''
        special_category = ''
        special_type = ''
        special_production = ''
        if 'category' in server_data:
            if 'name' in server_data['category']:
                special_category = server_data['category']['name']
        if 'type' in server_data:
            if 'name' in server_data['type']:
                special_type = server_data['type']['name']
        if 'method' in server_data:
            if 'name' in server_data['method']:
                special_production = server_data['method']['name']
        category_type_production = ''
        if special_category != '':
            category_type_production = str(special_category) + ', '
        if special_type != '':
            category_type_production += str(special_type) + ', '
        if special_production != '':
            category_type_production += str(special_production)
        server_data['category_type_production'] = category_type_production
        server_data['batch_info'] = 'Batch #: ' + '' + '; Batch Size: ' + str(server_data['initial_weight']) + ' - grams'
        server_data['initial_weight'] = str(server_data['initial_weight']) + ' grams'
        if server_data['date_received'] is None or server_data['date_received'] == 'null':
            date_received = ''
        else:
            date_received = server_data['date_received'].split(',')[1].split(' ')
            date_received = date_received[:-2]
            date_received = months[date_received[2]] + '/' + date_received[1] + '/' + date_received[3]
        if server_data['last_modified'] is None or server_data['last_modified'] == 'null':
            last_modified = ''
        else:
            last_modified = server_data['last_modified'].split(',')[1].split(' ')
            last_modified = last_modified[:-2]
            last_modified = months[last_modified[2]] + '/' + last_modified[1] + '/' + last_modified[3]
        if server_data['date_completed'] is None or server_data['date_completed'] == 'null':
            date_completed = ''
            expires = ''
        else:
            complete_split = server_data['date_completed'].split('/')
            year = complete_split[2]
            year2 = int(year) + 1
            year3 = str(year2)
            expires = str(complete_split[0]) + '/' + str(complete_split[1]) + '/' + year3
            # date_completed = server_data['date_completed'].split(',')[1].split(' ')
            # date_completed = date_completed[:-2]
            # expires = server_data['date_completed'].split(',')[1].split(' ')
            # year = server_data['date_completed'].split(',')[1].split(' ')
            # year = year[:-2]
            # year = str(year[-1])
            # expires = str(expires[:-3]) + ' ' + str(int(year) + 1)
            # date_completed = date_completed[2] + ' ' + date_completed[1] + ', '
        date_completed = server_data['date_completed']
        if str(date_completed) == '':
            server_data['bunch_of_dates'] = 'Ordered: ' + str(date_received) + '; Sampled: ' + str(last_modified)
        else:
            server_data['bunch_of_dates'] = 'Ordered: ' + str(date_received) + '; Sampled: ' + str(last_modified) + '; Completed: ' + str(date_completed) + '; Expires: ' + str(expires)
        server_data['type_and_method'] = str(server_data['type']['name']) + ', ' + str(server_data['method']['name'])
        server_data['lab']['full_street_address'] = str(server_data['lab']['address_line_1']) + ' ' + str(server_data['lab']['address_line_2'])
        server_data['lab']['city_state_zip'] = str(server_data['lab']['city'].title()) + ', ' + str(server_data['lab']['state']) + ' ' + str(server_data['lab']['zipcode'])
        server_data['client']['city_state_zip'] = str(server_data['client_info']['city'].title()) + ', ' + str(server_data['client_info']['state']) + ' ' + str(server_data['client_info']['zipcode'])
        server_data['special'] = {}
        server_data['date_received'] = date_received
        server_data['last_modified'] = last_modified

        ###################################
        server_data['sample_collection'] = ''
        server_data['environment'] = ''
        server_data['total_pesticide_ppms'] = ''
        server_data['notes'] = ''
        server_data['microscope_image'] = ''
        server_data['total_solvent_ppms'] = ''
        server_data['total_cannabinoids'] = ''
        server_data['special']['foreign_matter'] = ''
        server_data['misc'] = {}
        server_data['misc']['insects_value'] = ''
        server_data['misc']['mites_value'] = ''
        server_data['misc']['mold_value'] = ''
        server_data['misc']['other_value'] = ''
        server_data['cbg_cbga_cbc_cbn_total'] = ''
        server_data['special']['water_activity'] = ''
        ############################################
        server_data['pesticides_badge'] = ''
        server_data['microbials_badge'] = ''
        server_data['sgs_score'] = ''
        server_data['solvents_badge'] = ''
        server_data['foreign_matter_badge'] = ''
        ############################################

        r_units = server_data['lab_data']['cannabinoids']['report_units']
        try:
            server_data['client_license']['license_number'] = 'Lic. # ' + str(server_data['client_license']['license_number'])
        except Exception as e:
            print str(e)
            pass
        try:
            special_cbd_total = str(server_data['lab_data']['cannabinoids']['cbd_total']['display'][r_units]['value'])
            if special_cbd_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
                special_cbd_total = round(float(special_cbd_total), 1)
                special_cbd_total = str(special_cbd_total)
                special_cbd_total = special_cbd_total + str(r_units)
            special_thc_total = str(server_data['lab_data']['thc']['thc_total']['display'][r_units]['value'])
            if special_thc_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
                special_thc_total = round(float(special_thc_total), 1)
                special_thc_total = str(special_thc_total)
                special_thc_total = special_thc_total + str(r_units)
        except Exception as e:
            print str(e)
            special_cbd_total = ''
            special_thc_total = ''
            pass
        try:
            special_moisture = str(server_data['lab_data']['moisture']['tests']['percent_moisture']['display']['%']['value'])
            if str(special_moisture) != '' and str(special_moisture) not in ['ND', 'NR']:
                special_moisture = round(float(special_moisture), 1)
                special_moisture = str(special_moisture)
                special_moisture = str(special_moisture) + '%'
        except Exception as e:
            print str(e)
            pass
            special_moisture = ''

        new_unit = str(r_units)
        if r_units != '%':
            new_unit = ' ' + r_units

        server_data['special'] = {
            'total_thc': str(special_thc_total),
            'total_cbd': str(special_cbd_total),
            'moisture': str(special_moisture)
        }
    except Exception as e:
        print str(e)
        print "this is a concat section issue"

    for category in test_categories:
        print "we're on category ------------------->  " + category
        try:
            digits = server_data['lab_data'][category]['digits']
            report_units = server_data['lab_data'][category]['report_units']
            secondary_report_units = 'mg/g'
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
                server_data['special']['total_cannabinoids'] = str(total_cannabinoid_concentration) + str(report_units)
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
                server_data['lab_data']['cannabinoids']['tests'] = new_test_data
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
                server_data['category_units'][category] = [
                    report_units,
                    secondary_report_units
                ]
                new_test_data = add_units_to_values(category_data)
                server_data['lab_data'][category]['tests'] = new_test_data
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
                server_data['category_units'][category] = [
                    report_units,
                    secondary_report_units
                ]
                new_test_data = add_units_to_values(category_data)
                server_data['lab_data'][category]['tests'] = new_test_data
        except Exception as e:
            print "made it to the coa exception"
            print str(e)
            continue
        # category_data = server_data['lab_data'][category]['tests']

    if 'thc' in server_data['lab_data']:
        if 'tests' in server_data['lab_data']['thc']:
            thc_data = server_data['lab_data']['thc']['tests']
            new_test_data = add_units_to_values(thc_data)
            server_data['lab_data']['thc']['tests'] = new_test_data
    server_data['lab_data_latest'] = server_data['lab_data']
    server_data['viz'] = viztypes
    print "Initializing S3TemplateService"

    if os.path.exists('/tmp/work'):
        shutil.rmtree('/tmp/work')
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
    print "test_packages:"
    print server_data['test_packages']
    template_keys = get_test_packages(server_data['test_packages'])
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
