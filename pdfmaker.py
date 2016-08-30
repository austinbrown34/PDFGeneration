import pdftools as pdftools
import os


class PDFMaker(object):

    def __init__(self, templates, server_data):
        self.work_dir = '/tmp/work'
        self.templates = templates
        self.server_data = server_data
        self.total_pages = len(templates)
        os.environ['LD_LIBRARY_PATH'] = os.path.joing(os.getcwd(), 'bin', 'libgcj.so.10')

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
        for i, template in enumerate(templates):
            pdf = self.make_page(template, page_count)
            pdfs.append(pdf)
            page_count += 1
        print "about to merge"
        pdftools.merge_all_pages(pdfs, '/tmp/Final_PDF.pdf')
        print "merged and trying to open"
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
        #print str(fields)
        for i, e in enumerate(fields):
           # print e
            keys = e.split('.')
            #print str(keys)
            final_key = keys[-1]
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
        DTdata = server_data['datatable']
        SLdata = server_data['sparkline']

        ph_translation = pdftools.translate_placeholders(
            image_info,
            server_data,
            work_dir,
            page_count
        )
        print "ph_translation"
        print ph_translation

        DTdimensions = ph_translation['DTdimensions']
        DTcoords = ph_translation['DTcoords']
        SLdimensions = ph_translation['SLdimensions']
        SLcoords = ph_translation['SLcoords']
        ServerImages = ph_translation['ServerImages']
        vizfiles = []
        vizpdfs = []
        if DTcoords != []:
            pdftools.update_data_visualization(
                'js/datatable.js', DTdata, DTdimensions, DTcoords)
            vizfiles.append('html/datatable3.html')
            vizpdfs.append(os.path.join(work_dir, 'temp', 'datatable3.pdf'))
        if SLcoords != []:
            pdftools.update_data_visualization(
                'js/sparkline.js', SLdata, SLdimensions, SLcoords)
            vizfiles.append('html/sparkline5.html')
            vizpdfs.append(os.path.join(work_dir, 'temp', 'sparkline5.pdf'))

        #vizfiles = ['datatable3.html', 'sparkline3.html']
       # vizpdfs = [
       #     os.path.join(work_dir, 'temp', 'datatable3.pdf'),
       #     os.path.join(work_dir, 'temp', 'sparkline3.pdf')
       #     ]
        print "vizpdfs: "
        print vizpdfs
        if vizpdfs != []:
            fixed_vizpdfs = []
            pdftools.generate_visualizations(vizfiles, 'js/report3.js',  '/tmp/work/temp/')
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
