import os
from decimal import Decimal
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
    try:
        special_moisture = str(data['special']['moisture'])
        special_moisture = make_number(special_moisture.replace('%', ''), 3, True)
        if str(special_moisture) != '' and str(special_moisture) not in ['ND', 'NR']:
                special_moisture = str(special_moisture) + '%'
        data['special']['moisture'] = special_moisture
    # try:
    #     cannabinoid_datatable_data = data['viz']['datatable_cannabinoids']
    #     new_cannabinoid_datatable_data = []
    #     for i, analyte_data in enumerate(cannabinoid_datatable_data):
    #         new_analyte_data = [analyte_data[0], analyte_data[2], analyte_data[3]]
    #         new_cannabinoid_datatable_data.append(new_analyte_data)
    #     new_data['viz']['datatable_cannabinoids-scp'] = new_cannabinoid_datatable_data
    except Exception as e:
        print str(e)
        print "made it to the scepterformatting exception"
        pass
    response = {'data': new_data, 'templates': new_templates}
    return response
