from flask import Flask, jsonify, make_response, request, url_for, abort
import os
import requests
import sys
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter
import lxml.etree
from PIL import Image as IMG
import piexif
from fdfgen import forge_fdf
import subprocess
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Image
from reportlab.lib.utils import ImageReader
import urllib2
import shutil
from io import BytesIO
from pdfminer.pdftypes import LITERALS_DCT_DECODE
from pdfminer.pdfcolor import LITERAL_DEVICE_GRAY
from pdfminer.pdfcolor import LITERAL_DEVICE_RGB
from pdfminer.pdfcolor import LITERAL_DEVICE_CMYK
import boto3
import yaml
import threading
import time
import json

session = boto3.Session(
    aws_access_key_id='AKIAI5NYJC5SDJ3NKVIQ',
    aws_secret_access_key='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'
)
s3 = session.resource('s3')

app = Flask(__name__)


class BackgroundBuild(threading.Thread):

    def __init__(self, serverData):
        threading.Thread.__init__(self)
        self.serverData = serverData
        self.run()

    def run(self):
        serverData = self.serverData
        lab_abbrev = serverData['LAB_ABBREV']
        packages = serverData['TEST_PACKAGES']
        s3.meta.client.download_file(
            'pdfserver', 'cc/coa/' + lab_abbrev + '/config.yaml', 'config.yaml')
        cfg = open('config.yaml')
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        templates = []
        serverImageTags = ['SamplePhoto', 'QR', 'LabLogo', 'Signature']

        for package in packages:
            if package in cfg_obj:
                templates.append(cfg_obj[package])

        class MyImageWriter(object):

            def __init__(self, outdir):
                self.outdir = outdir
                self.jpgs = []
                if not os.path.exists(self.outdir):
                    os.makedirs(self.outdir)
                return

            def get_jpgs(self):
                return self.jpgs

            def export_image(self, image):
                stream = image.stream
                filters = stream.get_filters()
                (width, height) = image.srcsize
                if len(filters) == 1 and filters[0] in LITERALS_DCT_DECODE:
                    ext = '.jpg'
                    name = image.name + ext
                    path = os.path.join(self.outdir, name)
                    fp = file(path, 'wb')
                    raw_data = stream.get_rawdata()
                    fp.write(raw_data)
                    fp.close()
                    self.jpgs.append(image.name + ext)
                elif (image.bits == 1 or
                      image.bits == 8 and image.colorspace in (LITERAL_DEVICE_RGB, LITERAL_DEVICE_GRAY)):
                    ext = '.%dx%d.bmp' % (width, height)
                else:
                    ext = '.%d.%dx%d.img' % (image.bits, width, height)
                name = image.name + ext
                return name

        def get_acroform_fields(filename):
            fp = open(filename, 'rb')
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            field_names = []
            fields = resolve1(doc.catalog['AcroForm'])['Fields']
            for i in fields:
                field = resolve1(i)
                name, value = field.get('T'), field.get('V')
                field_names.append(name)
            return field_names

        def set_image_tag(filename, tag):
            exif_ifd = {
                piexif.ExifIFD.UserComment: unicode(tag)
            }
            exif_dict = {"Exif": exif_ifd}
            exif_bytes = piexif.dump(exif_dict)
            im = IMG.open(filename)
            im.save(filename, exif=exif_bytes)

        def get_image_tag(filename):
            tag = None
            try:
                exif_dict = piexif.load(filename)
                if piexif.ExifIFD.UserComment in exif_dict['Exif']:
                    tag = exif_dict['Exif'][
                        piexif.ExifIFD.UserComment].strip(' \t\r\n\0')
            except Exception as e:
                print filename + " has an unsupported format --- setting tag to None"
                print "Error: " + str(e)
            return tag

        def get_images(filename, jpg_names):
            pdf = file(filename, "rb").read()
            startmark = "\xff\xd8"
            startfix = 0
            endmark = "\xff\xd9"
            endfix = 2
            i = 0
            njpg = 0
            while True:
                istream = pdf.find("stream", i)
                if istream < 0:
                    break
                istart = pdf.find(startmark, istream, istream + 20)
                if istart < 0:
                    i = istream + 20
                    continue
                iend = pdf.find("endstream", istart)
                if iend < 0:
                    raise Exception("Didn't find end of stream!")
                iend = pdf.find(endmark, iend - 20)
                if iend < 0:
                    raise Exception("Didn't find end of JPG!")
                istart += startfix
                iend += endfix
                jpg = pdf[istart:iend]
                jpgfile = file('work/temp/' + jpg_names[njpg], "wb")
                jpgfile.write(jpg)
                jpgfile.close()
                njpg += 1
                i = iend

        def get_placeholder_image_info(filename, xmlfile, outputdir):
            if not os.path.isdir(outputdir):
                os.makedirs(outputdir)

            image_info = []
            password = ''
            caching = True
            rotation = 0
            fname = filename
            maxpages = 0
            pagenos = set()
            outputdir = outputdir
            placeholder_imgs = []
            outfile = os.path.join(outputdir, xmlfile)
            outfp = file(outfile, 'w')
            codec = 'utf-8'
            laparams = LAParams()
            imagewriter = MyImageWriter(outputdir)
            rsrcmgr = PDFResourceManager(caching=caching)
            device = XMLConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
                                  imagewriter=imagewriter)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            fp = file(fname, 'rb')
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            for page in PDFPage.get_pages(fp, pagenos,
                                          maxpages=maxpages, password=password,
                                          caching=caching, check_extractable=True):
                page.rotate = (page.rotate + rotation) % 360
                interpreter.process_page(page)

            fp.close()
            device.close()
            outfp.close()
            root = lxml.etree.parse(outfile)
            found_images = root.findall('.//image')
            found_image_boxes = root.xpath('.//figure[image]')
            jpg_count = 0
            for i, e in enumerate(found_images):
                imgpth = os.path.join(outputdir, e.attrib['src'])
                if not os.path.exists(imgpth):
                    print "path doesnt exist - tag is none for " + imgpth
                    tag = None
                else:
                    tag = get_image_tag(imgpth)
                    image_info.append({
                        "id": i,
                        "src": imgpth,
                        "height": e.attrib['height'],
                        "width": e.attrib['width'],
                        "bbox": found_image_boxes[i].attrib['bbox'],
                        "tag": tag
                    })
                    if tag is not None:
                        placeholder_imgs.append(jpg_count)
                    jpg_count += 1

            return {'image_info': image_info, 'placeholder_imgs': placeholder_imgs}

        def remove_all_images(filename, new_filename):
            args = [
                "gs",
                "-o",
                new_filename,
                "-sDEVICE=pdfwrite",
                "-dFILTERIMAGE",
                filename
            ]

            subprocess.call(args)

        def repair_pdf(broke_pdf, fixed_pdf):
            call = [
                'pdftk',
                broke_pdf,
                'output',
                fixed_pdf
            ]

            subprocess.call(call)

        def remove_placeholder_images(orig, newpdf, placeholder_imgs):
            pdf = file(orig, "rb").read()
            startmark = "\xff\xd8"
            startfix = 0
            endmark = "\xff\xd9"
            endfix = 2
            i = 0
            jpg_ranges = []
            njpg = 0
            mynewpdf = file(newpdf.replace('.pdf', '_temp.pdf'), "wb")
            while True:
                istream = pdf.find("stream", i)
                if istream < 0:
                    break
                istart = pdf.find(startmark, istream, istream + 20)
                if istart < 0:
                    i = istream + 20
                    continue
                iend = pdf.find("endstream", istart)
                if iend < 0:
                    raise Exception("Didn't find end of stream!")
                iend = pdf.find(endmark, iend - 20)
                if iend < 0:
                    raise Exception("Didn't find end of JPG!")

                istart += startfix
                iend += endfix
                if njpg in placeholder_imgs:
                    jpg_ranges.append([njpg, istart, iend])
                    jpg = pdf[istart:iend]
                    jpgfile = file('work/temp/'"jpg%d.jpg" % njpg, "wb")
                    jpgfile.write(jpg)
                    jpgfile.close()
                njpg += 1
                i = iend

            placeholder = 0
            for jpg_item in jpg_ranges:
                range_start = jpg_item[1]
                range_end = jpg_item[2]
                mynewpdf.write(pdf[placeholder:range_start])
                counter = range_start
                while counter < range_end + 1:
                    empty_bytes = bytes(1)
                    mynewpdf.write(empty_bytes)
                    counter += 1
                placeholder = range_end + 1
            mynewpdf.write(pdf[placeholder:sys.getsizeof(pdf)])
            mynewpdf.close()
            repair_pdf(newpdf.replace('.pdf', '_temp.pdf'), newpdf)

        def generate_fdf(fields, data, fdfname):
            field_value_tuples = []
            for field in fields:
                field_value = (field, data[field])
                field_value_tuples.append(field_value)
            fdf = forge_fdf("", field_value_tuples, [], [], [])
            fdf_file = open(fdfname, "wb")
            fdf_file.write(fdf)
            fdf_file.close()

        def fill_out_form(fdfname, template, filledname):

            call = [
                'pdftk',
                template,
                'fill_form',
                fdfname,
                'output',
                filledname,
                'flatten'
            ]

            subprocess.call(call)

        def update_data_visualization(data_vis_name, data, dimensions, coordinates):
            with open(data_vis_name, 'r') as file:
                content = file.readlines()

            content[1] = str(data) + ';\n'
            content[3] = str(dimensions) + ';\n'
            content[5] = str(coordinates) + ';\n'

            with open(data_vis_name, 'w') as file:
                file.writelines(content)

        def generate_visualizations(viz_files):
            for viz in viz_files:
                call = [
                    'phantomjs',
                    'report3.js',
                    viz,
                    'work/temp/' + viz.replace('html', 'pdf')
                ]
                subprocess.call(call)

        def draw_images_on_pdf(images, currentpdf, pdf_with_images):
            first = True
            counter = 1
            temp_imgs = []
            completed_temps = []
            for image in images:
                ext = image['serversource'].split('.')[-1]
                if ext == "jpg":
                    im = IMG.open(image['serversource'])
                    size = int(image['width']), int(image['height'])
                    im.thumbnail(size, IMG.ANTIALIAS)
                    im.save(image['serversource'].replace('.jpg','') + '_temp' + ext, "JPEG")
                    with IMG.open(image['serversource'].replace('.jpg','') + '_temp' + ext) as img:
                        width, height = im.size
                    diff = int(image['width']) - width
                    if diff != 0:
                        diff = diff/2
                else:
                    diff = 0
                    width = int(image['width'])
                    height = int(image['height'])
                c = canvas.Canvas(
                    'work/temp/tempimage' + str(counter) + '.pdf')
                c.drawImage(image['serversource'],
                            int(image['bbox'].split(',')[0].split('.')[0]) + diff,
                            int(image['bbox'].split(',')[1].split('.')[0]),
                            width=int(width),
                            height=int(height),
                            mask='auto')
                c.save()
                temp_imgs.append('work/temp/tempimage' +
                                 str(counter) + '.pdf')
                counter += 1
            counter = 1
            for tempimg in temp_imgs:
                print "tempimg: "
                print tempimg
                imagepdf = PdfFileReader(open(tempimg, 'rb'))
                output_file = PdfFileWriter()
                input_file = PdfFileReader(open(currentpdf, "rb"))
                page_count = input_file.getNumPages()
                for page_number in range(page_count):
                    print "Watermarking page {} of {}".format(page_number, page_count)
                    input_page = input_file.getPage(page_number)
                    input_page.mergePage(imagepdf.getPage(0))
                    output_file.addPage(input_page)
                with open('work/temp/temp' + str(counter) + '.pdf', "wb") as outputStream:
                    output_file.write(outputStream)
                    completed_temps.append(
                        'work/temp/temp' + str(counter) + '.pdf')
                currentpdf = 'work/temp/temp' + str(counter) + '.pdf'
                counter += 1

            os.rename(completed_temps[
                      len(completed_temps) - 1], pdf_with_images)

        def draw_visualization_on_pdf(vizs, currentpdf, pdf_with_vizs):
            counter = 1
            first = True
            for viz in vizs:
                if first is False:
                    currentpdf = 'work/temp/temp' + \
                        str(counter - 1) + '.pdf'
                vizpdf = PdfFileReader(open(viz, "rb"))
                output_file = PdfFileWriter()
                input_file = PdfFileReader(open(currentpdf, "rb"))
                page_count = input_file.getNumPages()
                for page_number in range(page_count):
                    print "Watermarking page {} of {}".format(page_number, page_count)
                    input_page = input_file.getPage(page_number)
                    input_page.mergePage(vizpdf.getPage(0))
                    output_file.addPage(input_page)

                if counter == len(vizs):
                    with open(pdf_with_vizs, "wb") as outputStream:
                        output_file.write(outputStream)
                else:
                    with open('work/temp/temp' + str(counter) + '.pdf', "wb") as outputStream:
                        output_file.write(outputStream)

                counter += 1
                first = False

        def merge_all_pages(pages, final):
            call = [
                'pdftk'
            ]
            for page in pages:
                call.append(page)
            call.append('cat')
            call.append('output')
            call.append(final)

            subprocess.call(call)
        def cycle_through_templates(templates, page_count, total_pages, finished_pages):
            for template in templates:
                page_count = str(page_count)
                s3.meta.client.download_file(
                    'pdfserver', 'cc/coa/' + lab_abbrev + '/' + template, 'work/' + template)

                serverData.update({'PageNumber': page_count, 'TotalPages': total_pages})
                fields = get_acroform_fields('work/' + template)
                print fields

                all_image_data = get_placeholder_image_info(
                    'work/' + template, 'work' + page_count + '.xml', 'work/temp')
                image_info = all_image_data['image_info']
                placeholder_imgs = all_image_data['placeholder_imgs']
                print image_info

                fielddata = {}
                for i in fields:
                    fielddata[i] = serverData[i]

                generate_fdf(fields, fielddata, 'work/temp/work' + page_count + '.fdf')

                fill_out_form('work/temp/work' + page_count + '.fdf', 'work/' +
                              template, 'work/temp/work_filled' + page_count + '.pdf')

                print "Placeholders: " + str(placeholder_imgs)

                remove_placeholder_images('work/temp/work_filled' + page_count + '.pdf',
                                          'work/temp/work_filled_noplaceholders' + page_count + '.pdf', placeholder_imgs)

                DTdata = []
                DTdimensions = []
                DTcoords = []
                SLdata = []
                SLdimensions = []
                SLcoords = []

                for analyte in serverData['LabData']:
                    DTdata.append([str(analyte), float(serverData['LabData'][analyte]['loq']), float(serverData[
                                  'LabData'][analyte]['mass1']), float(serverData['LabData'][analyte]['mass2'])])
                    SLdata.append(float(serverData['LabData'][analyte]['mass2']))

                serverImages = []

                for image in image_info:
                    img_spec = image
                    if img_spec['tag'] == 'DataTable':
                        DTdimensions = [int(img_spec['width']),
                                        int(img_spec['height'])]
                        x = img_spec['bbox'].split(",")[0].split('.')[0]
                        y = img_spec['bbox'].split(",")[1].split('.')[0]
                        DTcoords = [int(x), int(y)]
                    if img_spec['tag'] == 'SparkLine':
                        SLdimensions = [int(img_spec['width']),
                                        int(img_spec['height'])]
                        x = img_spec['bbox'].split(",")[0].split('.')[0]
                        y = img_spec['bbox'].split(",")[1].split('.')[0]
                        SLcoords = [int(x), int(y)]
                    if img_spec['tag'] in serverImageTags:
                        ext = '.' + \
                            serverData['Images'][img_spec['tag']].split(".")[-1]
                        remote_file = urllib2.urlopen(
                            serverData['Images'][img_spec['tag']])
                        with open('work/temp/' + img_spec['tag'] + page_count + ext, 'wb') as local_file:
                            shutil.copyfileobj(remote_file, local_file)
                        img_spec['serversource'] = 'work/temp/' + \
                            img_spec['tag'] + page_count + ext
                        serverImages.append(img_spec)

                update_data_visualization(
                    'datatable.js', DTdata, DTdimensions, DTcoords)
                update_data_visualization(
                    'sparkline.js', SLdata, SLdimensions, SLcoords)

                vizfiles = ['datatable.html', 'sparkline.html']
                vizpdfs = ['work/temp/datatable.pdf',
                           'work/temp/sparkline.pdf']

                fixed_vizpdfs = []
                generate_visualizations(vizfiles)
                for v in vizpdfs:
                    new_v = v.split('.')[0] + '_fixed.pdf'
                    repair_pdf(v, new_v)
                    fixed_vizpdfs.append(new_v)
                draw_images_on_pdf(serverImages, 'work/temp/work_filled_noplaceholders' + page_count + '.pdf',
                                   'work/temp/work_filled_with_images' + page_count + '.pdf')

                draw_visualization_on_pdf(
                    fixed_vizpdfs, 'work/temp/work_filled_with_images' + page_count + '.pdf', 'work/work_complete' + page_count + '.pdf')

                finished_pages.append('work/work_complete' + page_count + '.pdf')
                page_count = int(page_count)
                page_count += 1

            merge_all_pages(finished_pages, 'work/finalreport.pdf')
            return

        finished_pages = []
        page_count = 1
        all_templates = []
        def get_all_templates(templates):
            for template in templates:
                if not isinstance(template, (str, unicode)):
                    get_all_templates(template)
                    continue
                all_templates.append(template)
        get_all_templates(templates)
        total_pages = len(all_templates)
        cycle_through_templates(all_templates, page_count, total_pages, finished_pages)
        print 'Uploading PDF to S3'

        s3.meta.client.upload_file(
            "work/finalreport.pdf", 'pdfserver', 'cc/coa/' + lab_abbrev + '/finalreport.pdf')
        url = serverData['Callback']
        client = session.client('s3')
        file_url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': 'pdfserver',
                'Key': 'cc/coa/' + lab_abbrev + '/finalreport.pdf'
            }
        )
        pdfdata = {'Rendered_Report': file_url}
        headers = {'Content-Type': 'application/json'}
        requests.post(url, data=json.dumps(pdfdata), headers=headers)
        subprocess.call('rm -rf /home/ec2-user/PDFServer/work/*', shell=True)
        return




@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/PDFServer/api/v1.0/generate', methods=['POST'])
def generate_reports():
    if not request.json or not 'LAB_ABBREV' in request.json or not 'TEST_PACKAGES' in request.json or not 'Callback' in request.json:
        abort(400)
    serverData = request.json
    builder = BackgroundBuild(serverData)
    builder.start()
    return jsonify({'result': 'Request Received'})


@app.route('/')
def hello_world():
    return 'Hello Worlds!'

if __name__ == '__main__':
    app.run()
