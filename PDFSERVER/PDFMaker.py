import PDFTools as pdftools
import os


class PDFMaker(object):

    def __init__(self, templates, server_data):
        self.work_dir = 'work'
        self.templates = templates
        self.server_data = server_data
        self.total_pages = len(templates)
        self.work_dir = work_dir

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

        pdftools.merge_all_pages(pdfs, 'Final_PDF.pdf')
        final_pdf = open('Final_PDF.pdf', 'rb').read()
        return final_pdf

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
        pdftools.download_template(template)
        fields = pdftools.get_acroform_fields(os.path.join(work_dir, template))
        all_image_data = pdftools.get_placeholder_image_info(
            os.path.join(work_dir, template),
            'work' + page_count + '.xml',
            os.path.join(work_dir, 'temp'))
        image_info = all_image_data['image_info']
        placeholder_imgs = all_image_data['placeholder_imgs']
        fielddata = {}
        fieldvalues = pdftools.map_variables(fields, server_data)
        for i, e in enumerate(fields):
            fielddata[e] = fieldvalues[i]
        pdftools.generate_fdf(
            fields,
            fielddata,
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'))
        pdftools.fill_out_form(
            os.path.join(work_dir, 'temp', 'work' + page_count + '.fdf'),
            os.path.join(work_dir, template),
            os.path.join(work_dir, 'temp', 'work_filled' + page_count + '.pdf')
            )
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
            placeholder_imgs)

        DTdata = pdftools.build_visualization(server_data['datatable'])
        SLdata = pdftools.build_visualization(server_data['sparkline'])

        ph_translation = pdftools.translate_placeholders(
            image_info,
            server_data,
            work_dir,
            page_count
        )
        DTdimensions = ph_translation['DTdimensions']
        DTcoords ph_translation['DTcoords']
        SLdimensions = ph_translation['SLdimensions']
        SLcoords = ph_translation['SLcoords']
        SeverImages = ph_translation['ServerImages']

        pdftools.update_data_visualization(
            'datatable.js', DTdata, DTdimensions, DTcoords)
        pdftools.update_data_visualization(
            'sparkline.js', SLdata, SLdimensions, SLcoords)

        vizfiles = ['datatable.html', 'sparkline.html']
        vizpdfs = [
            os.path.join(work_dir, 'temp', 'datatable.pdf'),
            os.path.join(work_dir, 'temp', 'sparkline.pdf')
            ]

        fixed_vizpdfs = []
        pdftools.generate_visualizations(vizfiles)
        for v in vizpdfs:
            new_v = v.split('.')[0] + '_fixed.pdf'
            pdftools.repair_pdf(v, new_v)
            fixed_vizpdfs.append(new_v)
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
            )
        )

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
            )
        )

        return os.path.join(work_dir, 'work_complete' + page_count + '.pdf')
