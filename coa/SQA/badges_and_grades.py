def run(data):
    new_data = data
    new_data['general_micro_grade'] = 'Fail'
    new_data['advanced_micro_grade'] = 'A'
    new_data['solvents_grade'] = '5 Tree'
    automatic_fail = False
    if 'solvents' in data['lab_data']:
        total_ppms = 0.0
        for analyte in data['lab_data']['solvents']:
            value = data['lab_data']['solvents']['tests'][analyte]['display']['ppm']['value']
            try:
                value = float(value)
            except Exception as e:
                print str(e)
                value = 0.0
                pass

            total_ppms += value
            if analyte in ['acetone', 'n_butane', 'ethanol', 'heptane', 'iso_butane', 'isopentane', 'isoproponol', 'pentane', 'propane']:
                if data['lab_data']['microbials']['tests'][analyte]['display']['ppm']['value'] > 5000:
                    automatic_fail = True
            if analyte == 'acetonitrile':
                if data['lab_data']['microbials']['tests'][analyte]['display']['ppm']['value'] > 410:
                    automatic_fail = True
            if analyte == 'hexane':
                if data['lab_data']['microbials']['tests'][analyte]['display']['ppm']['value'] > 280:
                    automatic_fail = True
            if analyte == 'methanol':
                if data['lab_data']['microbials']['tests'][analyte]['display']['ppm']['value'] > 3000:
                    automatic_fail = True


        if total_ppms > 0 and total_ppms < 51:
            new_data['solvents_grade'] = '4 Tree'
        if total_ppms > 50 and total_ppms < 501:
            new_data['solvents_grade'] = '3 Tree'
        if total_ppms > 500 and total_ppms < 5001:
            new_data['solvents_grade'] = '2 Tree'
        if total_ppms > 5000:
            new_data['solvents_grade'] = '1 Tree'

        if automatic_fail is True:
                new_data['advanced_micro_grade'] = 'F'
    automatic_fail = False
    if 'microbials' in data['lab_data']:
        if 'mold' in data['lab_data']['microbials']['tests'] and 'aerobic_bacteria' in data['lab_data']['microbials']['tests']:
            if data['lab_data']['microbials']['tests']['mold']['display']['cfu/g']['value'] < 10000 and data['lab_data']['microbials']['tests']['aerobic_bacteria']['display']['cfu/g']['value'] < 100000:
                new_data['general_micro_grade'] = 'Pass'
        total_cfus = 0.0
        for analyte in data['lab_data']['microbials']:
            value = data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value']
            try:
                value = float(value)
            except Exception as e:
                print str(e)
                value = 0.0
                pass

            total_cfus += value
            if analyte == 'ecoli':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 10:
                    automatic_fail = True
            if analyte == 'salmonella':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 10:
                    automatic_fail = True
            if analyte == 'lysteria':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 100:
                    automatic_fail = True
            if analyte == 'pseudomonas':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 100:
                    automatic_fail = True
            if analyte == 'mold':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 10000:
                    automatic_fail = True
            if analyte == 'aerobic_bacteria':
                if data['lab_data']['microbials']['tests'][analyte]['display']['cfu/g']['value'] > 100000:
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




    new_data['badges'] = {
        'good': True,
        'bad': False
        }
    return new_data
