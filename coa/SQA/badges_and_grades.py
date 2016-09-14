import os
def run(data, templates, s3templates):
    new_data = data
    new_templates = templates

    try:
        new_data['misc']['insects_value'] = new_data['lab_data']['misc']['misc_insects']
        new_data['misc']['mites_value'] = new_data['lab_data']['misc']['misc_Mites']
        new_data['misc']['mold_value'] = new_data['lab_data']['misc']['misc_mold']
        new_data['misc']['other_value'] = new_data['lab_data']['misc']['misc_other']
        foreign_matter_score = new_data['lab_data']['misc']['misc_1']
        if int(foreign_matter_score) == 5:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaFiveTree.png'
        elif int(foreign_matter_score) == 4:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaFourTree.png'
        elif int(foreign_matter_score) == 3:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaThreeTree.png'
        elif int(foreign_matter_score) == 2:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaTwoTree.png'
        elif int(foreign_matter_score) == 1:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaOneTree.png'
        else:
            foreign_matter_badge = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/blank.png'

        new_data['foreign_matter_badge'] = foreign_matter_badge
        if 'tests' in data['lab_data']['cannabinoids']:
            if data['lab_data']['cannabinoids']['tests'] != {}:
                new_data['lab_data']['thc']['thc_total']['display']['%']['value'] = str(new_data['lab_data']['thc']['thc_total']['display']['%']['value']) + '%'
                new_data['lab_data']['cannabinoids']['cbd_total']['display']['%']['value'] = str(new_data['lab_data']['cannabinoids']['cbd_total']['display']['%']['value']) + '%'
                total_other_cannabinoids = 0.0
                total_cannabinoids = 0.0
                total_thc_analytes = 0.0
                for analyte in data['lab_data']['thc']['tests']:
                    value = data['lab_data']['thc']['tests'][analyte]['display']['%']['value']
                    value = value.replace('%', '')
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass
                    if analyte in ['thc', 'thca', 'cbd', 'cbda', 'cbg', 'cbga', 'cbc', 'cbn']:
                        total_thc_analytes += value

                for analyte in data['lab_data']['cannabinoids']['tests']:
                    value = data['lab_data']['cannabinoids']['tests'][analyte]['display']['%']['value']
                    value = value.replace('%', '')
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass
                    if analyte in ['thc', 'thca', 'cbd', 'cbda', 'cbg', 'cbga', 'cbc', 'cbn']:
                        total_cannabinoids += value
                    if analyte in ['cbg', 'cbga', 'cbc', 'cbn']:
                        total_other_cannabinoids += value
                new_data['cbg_cbga_cbc_cbn_total'] = str(total_other_cannabinoids) + '%'
                combined_cannabinoids = total_thc_analytes + total_cannabinoids
                new_data['total_cannabinoids'] = str(combined_cannabinoids) + '%'
                try:
                    moisture = str(data['special']['moisture']).replace('%', '')
                    moisture = float(moisture)
                except Exception as e:
                    print str(e)
                    moisture = 0.0
                    pass
                other_matter_value = 100 - moisture - total_cannabinoids
                new_data['other_matter'] = str(other_matter_value) + '%'

        if '1HPLCEdible.pdf' in templates or '2HPLCReport.pdf' in templates:
            new_templates = []
            for template in templates:
                if template == '1GCEdible.pdf':
                    new_templates.append('1HPLCEdible.pdf')
                elif template == '1GCReport.pdf':
                    new_templates.append('2HPLCReport.pdf')
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
                    value = value.lower().replace('ppm', '').strip()
                    try:
                        value = float(value)
                    except Exception as e:
                        print str(e)
                        value = 0.0
                        pass

                    total_ppms += value
                new_data['total_pesticide_ppms'] = str(int(round(total_ppms, 0))) + ' PPM'
                if total_ppms > 20:
                    new_data['pesticides_badge'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/fail.png'
        if 'tests' in data['lab_data']['solvents']:
            if data['lab_data']['solvents']['tests'] != {}:
                new_data['solvents_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/SequoiaFiveTree.png'
                total_ppms = 0.0
                for analyte in data['lab_data']['solvents']['tests']:
                    value = data['lab_data']['solvents']['tests'][analyte]['display']['ppm']['value']
                    value = value.lower().replace('ppm', '').strip()
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

                new_data['total_solvent_ppms'] = str(int(round(total_ppms, 0))) + ' PPM'
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
                    if float(data['lab_data']['microbials']['tests']['mold']['display']['cfu/g']['value'].lower().replace('cfu/g', '')) < 10000 and float(data['lab_data']['microbials']['tests']['aerobic_bacteria']['display']['cfu/g']['value'].lower().replace('cfu/g', '')) < 100000:
                        new_data['general_micro_grade'] = 'https://s3-us-west-2.amazonaws.com/cc-pdfserver/coa/SQA/assets/Gold+Edit.png'
                total_cfus = 0.0
                for analyte in data['lab_data']['microbials']['tests']:
                    value = data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value']
                    value = value.lower().replace('cfu/g', '').strip()
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
