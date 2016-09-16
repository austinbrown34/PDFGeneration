import pdftools as pdftools
import os


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
        print "about to merge"
        print "contents of work dir:"
        print os.listdir('/tmp/work/')
        print "contents of work/temp dir:"
        print os.listdir('/tmp/work/temp/')
        pdftools.merge_all_pages(pdfs, '/tmp/Final_PDF.pdf')
        pdftools.get_fonts()
        print "merged and trying to open"
        pdftools.repair_pdf('/tmp/Final_PDF.pdf', '/tmp/Final_PDF.pdf')
        final_pdf = open('/tmp/Final_PDF.pdf', 'rb')
        response = {
            'status': 'PDF Generated Successfully',
            'pdf': final_pdf
        }
        print response['status']
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
        if not os.path.isdir(work_dir):
            os.makedirs(work_dir)
        print "about to get fields........................................."
        fields = pdftools.get_acroform_fields_pdftk(os.path.join(work_dir, template))
        #print fields
        print "got fields..........................................."
        all_image_data = pdftools.get_placeholder_image_info(
            os.path.join(work_dir, template),
            'work' + page_count + '.xml',
            os.path.join(work_dir, 'temp'))
        image_info = all_image_data['image_info']
        placeholder_imgs = all_image_data['placeholder_imgs']
        print "Placeholder images:"
        print placeholder_imgs
        fielddata = {}
        fieldvalues = pdftools.map_variables(fields, server_data)
        print "This is your fielddata"
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
        print str(fielddata)
        pdftools.generate_fdf(
            fields,
            fielddata,
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'))
        print "generated fdf"
        pdftools.fill_out_form(
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'),
            os.path.join(work_dir, template),
            os.path.join(work_dir, 'temp', 'work_filled' + page_count + '.pdf')
            )
        print "filled out form"
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
        print "removed placeholder imgs"


        ph_translation = pdftools.translate_placeholders(
            image_info,
            server_data,
            work_dir,
            page_count
        )
        print "ph_translation"
        print ph_translation

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
                if viz['viz_file'].endswith('_with_sparkline.html'):
                    js_filename = os.path.join(
                        'job_types',
                        server_data['viz']['job_type'],
                        viz['viz_folder'],
                        viz['viz_type'],
                        'js',
                        viz['viz_type'] + '_sparkline.js')

                js_data.append([
                    js_filename,
                    viz['viz_data'],
                    viz['viz_dimensions'],
                    viz['viz_coords'],
                    server_data['category_units'][viz['viz_specific'].split('_')[1]][0],
                    server_data['category_units'][viz['viz_specific'].split('_')[1]][1]
                ])
                pdftools.update_data_visualization(
                    js_filename,
                    viz['viz_data'],
                    viz['viz_dimensions'],
                    viz['viz_coords'],
                    server_data['category_units'][viz['viz_specific'].split('_')[1]][0],
                    server_data['category_units'][viz['viz_specific'].split('_')[1]][1]
                )
                viz_file = os.path.join(
                    'job_types',
                    server_data['viz']['job_type'],
                    viz['viz_folder'],
                    viz['viz_type'],
                    'html',
                    viz['viz_file'])
                vizfiles.append(viz_file)
                name_of_pdf = os.path.join(work_dir, 'temp', viz['viz_specific'] + '.pdf')
                if name_of_pdf in vizpdfs:
                    pdfcounter += 1
                    name_of_pdf = os.path.join(work_dir, 'temp', viz['viz_specific'] + str(pdfcounter) + '.pdf')
                vizpdfs.append(name_of_pdf)
                pdftools.generate_visualization(viz_file, 'report.js', '/tmp/work/temp/', name_of_pdf)


        print "vizpdfs: "
        print vizpdfs
        fixed_vizpdfs = []
        if vizpdfs != []:
            # if pdfcounter > 1:
            #     pdftools.generate_visualizations(vizfiles, 'report.js',  '/tmp/work/temp/', vizpdfs)
            # else:
            #     pdftools.generate_visualizations(vizfiles, 'report.js',  '/tmp/work/temp/')
            for v in vizpdfs:
                new_v = v.split('.')[0] + '_fixed.pdf'
                print "---------------"
                print v
                print new_v
                print "---------------"
                pdftools.repair_pdf(v, new_v)
                fixed_vizpdfs.append(new_v)
        print "fixed_vizpdfs: "
        print fixed_vizpdfs
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
        print "images drawn and viz is starting"
        if fixed_vizpdfs == []:
            with open(os.path.join(work_dir, 'work_complete' + page_count + '.pdf'), 'wb') as output:
                output.write(open(os.path.join(work_dir, 'temp', 'work_filled_with_images' + page_count + '.pdf'), 'rb').read())
        else:
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
        print "finised page"
        return os.path.join(work_dir, 'work_complete' + page_count + '.pdf')
