import os
def run(data, templates, s3templates):
    new_data = data
    new_templates = templates
    if '1HPLCEdible.pdf' in templates or '2HPLCReport.pdf' in templates:
        new_templates = []
        for template in templates:
            if template == '1GCEdible.pdf':
                new_templates.append('1HPLCEdible.pdf')
            elif template == '1GCReport.pdf':
                new_templates.append('1HPLCReport.pdf')
            elif template == '3GCReport2.pdf':
                new_templates.append('2HPLCReport2.pdf')
            else:
                new_templates.append(template)
        new_templates = list(set(new_templates))
        new_templates.sort()
        template_folder = new_data['lab']['abbreviation']
        print "downloading templates"
        print str(new_templates)
        s3templates.download_templates(os.path.join('coa', template_folder), new_templates)
    try:
        new_data['general_micro_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'
        new_data['advanced_micro_grade'] = ''
        new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'
        new_data['pesticides_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'
        new_data['foreign_matter_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'
        new_data['solvents_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'
        automatic_fail = False
        if 'tests' in data['lab_data']['pesticides']:
            if data['lab_data']['pesticides']['tests'] != {}:
                new_data['pesticides_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/Silver+Edit.png'
                total_ppms = 0.0
                for analyte in data['lab_data']['pesticides']['tests']:
                    value = data['lab_data']['pesticides']['tests'][analyte]['display']['ppm']['value']
                    value = value.replace('ppm', '')
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass

                    total_ppms += value
                if total_ppms > 20:
                    new_data['pesticides_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/fail.png'
        if 'tests' in data['lab_data']['solvents']:
            if data['lab_data']['solvents']['tests'] != {}:
                new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaFiveTree.png'
                total_ppms = 0.0
                for analyte in data['lab_data']['solvents']['tests']:
                    value = data['lab_data']['solvents']['tests'][analyte]['display']['ppm']['value']
                    value = value.replace('ppm', '')
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass

                    total_ppms += value
                    if analyte in ['acetone', 'n_butane', 'ethanol', 'heptane', 'iso_butane', 'isopentane', 'isoproponol', 'pentane', 'propane']:
                        if value > 5000:
                            automatic_fail = True
                    if analyte == 'acetonitrile':
                        if value > 410:
                            automatic_fail = True
                    if analyte == 'hexane':
                        if value > 280:
                            automatic_fail = True
                    if analyte == 'methanol':
                        if value > 3000:
                            automatic_fail = True


                if total_ppms > 0 and total_ppms < 51:
                    new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaFourTree.png'
                if total_ppms > 50 and total_ppms < 501:
                    new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaThreeTree.png'
                if total_ppms > 500 and total_ppms < 5001:
                    new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaTwoTree.png'
                if total_ppms > 5000:
                    new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaOneTree.png'

                if automatic_fail is True:
                        new_data['advanced_micro_grade'] = 'F'
        automatic_fail = False
        if 'tests' in data['lab_data']['microbials']:
            if data['lab_data']['microbials']['tests'] != {}:
                new_data['advanced_micro_grade'] = 'A'
                new_data['general_micro_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/fail.png'
                if 'mold' in data['lab_data']['microbials']['tests'] and 'aerobic_bacteria' in data['lab_data']['microbials']['tests']:
                    if float(data['lab_data']['microbials']['tests']['mold']['display']['cfu/g']['value'].replace('cfu/g', '')) < 10000 and float(data['lab_data']['microbials']['tests']['aerobic_bacteria']['display']['cfu/g']['value'].replace('cfu/g', '')) < 100000:
                        new_data['general_micro_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/Gold+Edit.png'
                total_cfus = 0.0
                for analyte in data['lab_data']['microbials']['tests']:
                    value = data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value']
                    value = value.replace('cfu/g', '')
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass

                    total_cfus += value
                    if analyte == 'ecoli':
                        if value> 10:
                            automatic_fail = True
                    if analyte == 'salmonella':
                        if value > 10:
                            automatic_fail = True
                    if analyte == 'lysteria':
                        if value > 100:
                            automatic_fail = True
                    if analyte == 'pseudomonas':
                        if value > 100:
                            automatic_fail = True
                    if analyte == 'mold':
                        if value > 10000:
                            automatic_fail = True
                    if analyte == 'aerobic_bacteria':
                        if value > 100000:
                            automatic_fail = True

                if total_cfus > 0 and total_cfus < 1000:
                    new_data['advanced_micro_grade'] = 'B'
                if total_cfus > 999 and total_cfus < 20000:
                    new_data['advanced_micro_grade'] = 'C'
                if total_cfus > 19999 and total_cfus < 100000:
                    new_data['advanced_micro_grade'] = 'D'
                if total_cfus > 99999:
                    new_data['advanced_micro_grade'] = 'F'

                if automatic_fail is True:
                    new_data['advanced_micro_grade'] = 'F'

        new_data['microbials_badge'] = new_data['general_micro_grade']
        new_data['solvents_badge'] = new_data['solvents_grade']
        new_data['sgs_score'] = new_data['advanced_micro_grade']

    except Exception as e:
        print str(e)
        print "made it to the badges_and_grades exception"
        pass
    response = {'data': new_data, 'templates': new_templates}
    return response
