import os
from decimal import getcontext, Decimal

# Set the precision.
getcontext().prec = 3
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

def make_number(data, digits=None, labels=False):
    try:
        data = float(data)
    except ValueError:
        if not labels:
            data = float(0)
        if data == "<LOQ":
            data = "&ltLOQ"

    output = data
    if digits is not None and isinstance(data, float):
        dec = Decimal(data)
        output = round(dec,int(digits))
    return output

def run(data, templates, s3templates):
    new_data = data
    new_templates = templates
    if '1-combo2.pdf' in templates or '1-combo4.pdf' in templates:
        try:
            new_data['category_units']['cannabinoids'] = [
                    'mg/g',
                    'mg/unit'
            ]
            digits = data['lab_data']['cannabinoids']['digits']
            cannabinoid_data = data['lab_data']['cannabinoids']['tests']
            thc_data = data['lab_data']['thc']['tests']
            combined_cannabinoids_dt = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    'cannabinoids', 'datatable', digits, 'mg/g', 'mg/unit')
            new_data['viz']['datatable_cannabinoids'] = combined_cannabinoids_dt
        except Exception as e:
            print str(e)
            print "made it to the modifying data for mca exception"
            pass
        try:
            special_cbd_total = str(data['lab_data']['cannabinoids']['cbd_total']['display']['mg/unit']['value'])
            special_thc_total = str(data['lab_data']['thc']['thc_total']['display']['mg/unit']['value'])
            if special_cbd_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
                special_cbd_total = special_cbd_total + str('mg/unit')
            if special_thc_total not in ['<LOQ', 'ND', 'NT', 'TNC', '<LOD']:
                special_thc_total = special_thc_total + str('mg/unit')
        except Exception as e:
            print str(e)
            print "made it to the mca-special exception"
            special_thc_total = ''
            special_cbd_total = ''
            pass
        new_data['special']['total_thc'] = special_thc_total
        new_data['special']['total_cbd'] = special_cbd_total
    response = {'data': new_data, 'templates': new_templates}
    return response
