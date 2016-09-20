import os
def run(data, templates, s3templates):
    new_data = data
    new_templates = templates

    try:
        cannabinoid_datatable_data = data['viz']['datatable_cannabinoids']
        new_cannabinoid_datatable_data = []
        for i, analyte_data in enumerate(cannabinoid_datatable_data):
            new_analyte_data = [analyte_data[0], analyte_data[2], analyte_data[3]]
            new_cannabinoid_datatable_data.append(new_analyte_data)
        new_data['viz']['datatable_cannabinoids-scp'] = new_cannabinoid_datatable_data
    except Exception as e:
        print str(e)
        print "made it to the scepterformatting exception"
        pass
    response = {'data': new_data, 'templates': new_templates}
    return response
