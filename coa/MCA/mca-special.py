import os
from decimal import getcontext, Decimal

# Set the precision.
getcontext().prec = 3

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
    if '1-combo2.pdf' in templates:
        try:
            new_data['category_units']['cannabinoids'] = [
                    'mg/g',
                    'mg/unit'
            ]
            revised_dt_data = []
            for analyte_data in data['viz']['datatable_cannabinoids']:
                if analyte_data[0].startswith('C'):
                    mgunit = str(data['lab_data_latest']['cannabinoids']['tests'][analyte_data[0]]['display']['mg/unit']['value'])
                elif analyte_data[0].startswith('T'):
                    mgunit = ''
                else:
                    mgunit = str(data['lab_data_latest']['thc']['tests'][analyte_data[0]]['display']['mg/unit']['value'])
                revised_dt_data.append([analyte_data[0], analyte_data[1], analyte_data[2], mgunit])
            new_data['viz']['datatable_cannabinoids'] = revised_dt_data
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
