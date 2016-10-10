import pdftools as pdftools
import os
import shutil

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PDFMaker(object):

    def __init__(self, templates, server_data):
        self.work_dir = '/tmp/work'
        self.templates = templates
        self.server_data = server_data
        self.total_pages = len(templates)

    def make_pages(
            self,
            templates=None,
            server_data=None,
            directory=None):
        if templates is None:
            templates = self.templates
        if server_data is None:
            server_data = self.server_data
        if directory is None:
            directory = self.work_dir
        pdfs = []
        page_count = 1
        server_data['total_pages'] = len(templates)
        server_data['current_page'] = 1

        for i, template in enumerate(templates):
            server_data['page_of_pages'] = str(server_data['current_page']) + ' of ' + str(server_data['total_pages'])
            pdf = self.make_page(template, page_count)
            pdfs.append(pdf)
            page_count += 1
            cur_page = server_data['current_page'] + 1
            server_data['current_page'] = cur_page
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 9: MERGE PAGES INTO FINAL PDF"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Attempting to Merge PDF Pages..."
        # print "contents of work dir:"
        # print os.listdir('/tmp/work/')
        # print "contents of work/temp dir:"
        # print os.listdir('/tmp/work/temp/')
        pdftools.merge_all_pages(pdfs, '/tmp/Final_PDF.pdf')
        # pdftools.get_fonts()
        print "Merged Successfully ----> Running Precautionary Repair on Final PDF..."
        pdftools.repair_pdf('/tmp/Final_PDF.pdf', '/tmp/Final_PDF_fixed.pdf')
        final_pdf = open('/tmp/Final_PDF_fixed.pdf', 'rb')
        response = {
            'status': 'PDF Generated Successfully',
            'pdf': final_pdf
        }
        print
        print bcolors.OKGREEN
        print bcolors.BOLD
        print "------------------------------------------"
        print response['status']
        print "------------------------------------------"
        print bcolors.ENDC
        print
        return response

    def make_page(
            self,
            template,
            page_count,
            server_data=None,
            work_dir=None):
        if server_data is None:
            server_data = self.server_data
        if work_dir is None:
            work_dir = self.work_dir
        page_count = str(page_count)
        # if os.path.isdir(work_dir):
        #     shutil.rmtree('/tmp/work')
        if not os.path.isdir(work_dir):
            os.makedirs(work_dir)

        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 1: FORM FIELDS"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Retrieving PDF Form Fields..."
        fields = pdftools.get_acroform_fields_pdftk(os.path.join(work_dir, template))
        #print fields
        print "Fields Received..."
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 2: PLACEHOLDER IMAGES"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Analyzing PDF for Placeholder Images..."
        all_image_data = pdftools.get_placeholder_image_info(
            os.path.join(work_dir, template),
            'work' + page_count + '.xml',
            os.path.join(work_dir, 'temp'))
        image_info = all_image_data['image_info']
        placeholder_imgs = all_image_data['placeholder_imgs']
        # print "Placeholder images:"
        # print placeholder_imgs
        fielddata = {}
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 3: TAG TRANSLATION & MAPPING"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Mapping Form Field and Placeholder Image Variables to Data Values..."
        fieldvalues = pdftools.map_variables(fields, server_data)
        # print "This is your fielddata"
        for i, e in enumerate(fields):
            # e = e.replace('.', '::')
            # keys = e.split(':')
            #print str(keys)
            # final_key = keys[-1]
            if fieldvalues[i] is not None:
               # print final_key
               # print fieldvalues[i]
                fielddata[e] = fieldvalues[i]
            else:
                fielddata[e] = fieldvalues[i]
        # print str(fielddata)
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 4: FILLING OUT THE FORM"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Attempting to Generate FDF..."
        pdftools.generate_fdf(
            fields,
            fielddata,
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'))
        print "Successfully Generated FDF... Attempting to Fill Form..."

        pdftools.fill_out_form(
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'),
            os.path.join(work_dir, template),
            os.path.join(work_dir, 'temp', 'work_filled' + page_count + '.pdf')
            )
        print "Successfully Filled and Flattened Form..."
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 5: REMOVING PLACEHOLDER IMAGES"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Attempting to Remove Placeholder Images..."
        pdftools.remove_placeholder_images(
            os.path.join(
                work_dir,
                'temp',
                'work_filled' +
                page_count +
                '.pdf'),
            os.path.join(
                work_dir,
                'temp',
                'work_filled_noplaceholders' + page_count + '.pdf'
                ),
            placeholder_imgs,
            os.path.join(work_dir, 'temp')
        )
        print "Successfully Removed Placeholder Images..."


        ph_translation = pdftools.translate_placeholders(
            image_info,
            server_data,
            work_dir,
            page_count
        )
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 6: DOWNLOAD/GENERATE PLACEHOLDER REPLACEMENTS"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Translating Placeholder Tags into Visualization Tags and Server Image Tags..."
        # print ph_translation

        Visualizations = ph_translation['Visualizations']
        ServerImages = ph_translation['ServerImages']
        vizfiles = []
        vizpdfs = []
        js_data = []
        pdfcounter = 1
        if Visualizations != []:
            for viz in Visualizations:
                js_filename = os.path.join(
                    'job_types',
                    server_data['viz']['job_type'],
                    viz['viz_folder'],
                    viz['viz_type'],
                    'js',
                    viz['viz_type'] + '.js')
                if viz['viz_file'].endswith('-sparkline.html'):
                    js_filename = os.path.join(
                        'job_types',
                        server_data['viz']['job_type'],
                        viz['viz_folder'],
                        viz['viz_file'].replace('.html', ''),
                        'js',
                        viz['viz_file'].replace('.html', '') + '.js')
                viz_specific = viz['viz_specific']
                if viz['viz_specific'].find('-') != -1:
                    viz_specific = viz_specific.split('-')[0]

                js_data.append([
                    js_filename,
                    viz['viz_data'],
                    viz['viz_dimensions'],
                    viz['viz_coords'],
                    server_data['category_units'][viz_specific.split('_')[1]][0],
                    server_data['category_units'][viz_specific.split('_')[1]][1]
                ])
                print "Attempting to Update JS Variables for Visualizations..."
                pdftools.update_data_visualization(
                    js_filename,
                    viz['viz_data'],
                    viz['viz_dimensions'],
                    viz['viz_coords'],
                    server_data['category_units'][viz_specific.split('_')[1]][0],
                    server_data['category_units'][viz_specific.split('_')[1]][1],
                    server_data[viz_specific.split('_')[1] + '_report_columns'],
                    viz_specific.split('_')[1],
                    server_data[viz_specific.split('_')[1] + '_report_columns2'],
                    server_data[viz_specific.split('_')[1] + '_report_columns3']
                )
                viztype = viz['viz_type']
                if viz['viz_file'].endswith('-sparkline.html'):
                    viztype = viz['viz_file'].replace('.html', '')

                viz_file = os.path.join(
                    'job_types',
                    server_data['viz']['job_type'],
                    viz['viz_folder'],
                    viztype,
                    'html',
                    viz['viz_file'])
                vizfiles.append(viz_file)
                name_of_pdf = os.path.join(work_dir, 'temp', viz['viz_specific'] + '.pdf')
                if name_of_pdf in vizpdfs:
                    pdfcounter += 1
                    name_of_pdf = os.path.join(work_dir, 'temp', viz['viz_specific'] + str(pdfcounter) + '.pdf')
                vizpdfs.append(name_of_pdf)
                print "Running PhantomJS to Generate Visualization..."
                pdftools.generate_visualization(viz_file, 'report.js', '/tmp/work/temp/', name_of_pdf)

        # print "--------------------------------------"
        # print "vizpdfs: "
        # print vizpdfs
        fixed_vizpdfs = []
        if vizpdfs != []:
            # if pdfcounter > 1:
            #     pdftools.generate_visualizations(vizfiles, 'report.js',  '/tmp/work/temp/', vizpdfs)
            # else:
            #     pdftools.generate_visualizations(vizfiles, 'report.js',  '/tmp/work/temp/')
            for v in vizpdfs:
                new_v = v.split('.')[0] + '_fixed.pdf'
                # print "---------------"
                # print v
                # print new_v
                # print "---------------"
                print "Running Precautionary Repair Process..."
                # print "------------------------------------------"
                pdftools.repair_pdf(v, new_v)
                fixed_vizpdfs.append(new_v)
        # print "fixed_vizpdfs: "
        # print fixed_vizpdfs
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 7: ADDING SERVER IMAGES TO PDF"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        print "Attempting to Draw Images on PDF..."
        pdftools.draw_images_on_pdf(
            ServerImages,
            os.path.join(
                work_dir,
                'temp',
                'work_filled_noplaceholders' + page_count + '.pdf'
            ),
            os.path.join(
                work_dir,
                'temp',
                'work_filled_with_images' + page_count + '.pdf'
            ),
            os.path.join(work_dir, 'temp')
        )
        print
        print bcolors.OKBLUE
        print bcolors.BOLD
        print "------------------------------------------"
        print "STEP 8: ADDING VISUALIZATIONS TO PDF"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        if fixed_vizpdfs == []:
            # print "Image"
            with open(os.path.join(work_dir, 'work_complete' + page_count + '.pdf'), 'wb') as output:
                output.write(open(os.path.join(work_dir, 'temp', 'work_filled_with_images' + page_count + '.pdf'), 'rb').read())
        else:
            "Attempting to Draw Visualization on PDF..."
            pdftools.draw_visualization_on_pdf(
                fixed_vizpdfs,
                os.path.join(
                    work_dir,
                    'temp',
                    'work_filled_with_images' + page_count + '.pdf'
                ),
                os.path.join(
                    work_dir,
                    'work_complete' + page_count + '.pdf'
                ),
                os.path.join(work_dir, 'temp')
            )
        print
        print bcolors.HEADER
        print bcolors.BOLD
        print "------------------------------------------"
        print "Finished Generating Page (" + page_count + " of " + str(self.total_pages) + ")"
        print "------------------------------------------"
        print bcolors.ENDC
        print
        return os.path.join(work_dir, 'work_complete' + page_count + '.pdf')
