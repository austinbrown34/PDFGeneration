import os
import sys
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
import lxml.etree
from PIL import Image as IMG
import piexif
from fdfgen import forge_fdf
import subprocess
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
from Services import ImageExtractorService
import urllib2
import shutil
import requests


def get_acroform_fields_pdftk(filename):
    print filename
    args = ['pdftk', filename, 'dump_data_fields', 'output', 'work/dump_data_fields.txt']
    subprocess.call(args)
    field_names = []
    with open('work/dump_data_fields.txt') as ddf:
        for line in ddf:
            if 'FieldName:' in line:
                field_names.append(line.split('FieldName: ')[1].strip())
    return field_names
    

def get_acroform_fields(filename):
    fp = open(filename, 'rb')
    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    field_names = []
    fields = resolve1(doc.catalog['AcroForm'])['Fields']
    for i in fields:
        field = resolve1(i)
        print field
        name = field.get('T')
        field_names.append(name)
    fp.close()
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
        print filename + " has an unsupported format - setting tag to None"
        print "Error: " + str(e)

    return tag


def get_images(filename, jpg_names, jpg_dir):
    pdf = file(filename, "rb").read()
    startmark = "\xff\xd8"
    startfix, i, njpg = 0, 0, 0
    endmark = "\xff\xd9"
    endfix = 2
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
        jpgfile = file(jpg_dir + jpg_names[njpg], "wb")
        jpgfile.write(jpg)
        jpgfile.close()
        njpg += 1
        i = iend


def get_placeholder_image_info(filename, xmlfile, outputdir):
    if not os.path.isdir(outputdir):
        os.makedirs(outputdir)

    image_info, placeholder_imgs = [], []
    password = ''
    caching = True
    rotation, maxpages, jpg_count = 0, 0, 0
    fname = filename
    pagenos = set()
    outfile = os.path.join(outputdir, xmlfile)
    outfp = file(outfile, 'w')
    codec = 'utf-8'
    laparams = LAParams()
    imagewriter = ImageExtractorService(outputdir)
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
    for i, e in enumerate(found_images):
        imgpth = os.path.join(outputdir, e.attrib['src'])
        if not os.path.exists(imgpth):
            print "path doesnt exist - tag is none for " + imgpth
            tag = None
        else:
            tag = get_image_tag(imgpth)
            print tag
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


def remove_placeholder_images(
        orig,
        newpdf,
        placeholder_imgs,
        jpg_dir):
    pdf = file(orig, "rb").read()
    startmark = "\xff\xd8"
    startfix, i, njpg, placeholder = 0, 0, 0, 0
    endmark = "\xff\xd9"
    endfix = 2
    jpg_ranges = []
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
            jpgfile = file(jpg_dir + "jpg%d.jpg" % njpg, "wb")
            jpgfile.write(jpg)
            jpgfile.close()
        njpg += 1
        i = iend

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


def update_data_visualization(
        data_vis_name,
        data,
        dimensions,
        coordinates):
    with open(data_vis_name, 'r') as file:
        content = file.readlines()

    content[1] = str(data) + ';\n'
    content[3] = str(dimensions) + ';\n'
    content[5] = str(coordinates) + ';\n'

    with open(data_vis_name, 'w') as file:
        file.writelines(content)


def generate_visualizations(viz_files, controljs, out_dir):
    for viz in viz_files:
        print "from generate viz - viz, controljs, out_dir"
        print viz
        print controljs
        print out_dir
        
        call = [
            'phantomjs',
            controljs,
            viz,
            out_dir + viz.split('/')[-1].replace('.html', '.pdf')
        ]
        subprocess.call(call)


def draw_images_on_pdf(
        images,
        currentpdf,
        pdf_with_images,
        work_dir):
    counter = 1
    temp_imgs, completed_temps = [], []
    for image in images:
        ext = image['serversource'].split('.')[-1]
        if ext == "jpg":
            im = IMG.open(image['serversource'])
            size = int(image['width']), int(image['height'])
            im.thumbnail(size, IMG.ANTIALIAS)
            im.save(image['serversource'].replace('.jpg', '') +
                    '_temp' + ext, "JPEG")
            with IMG.open(
                    image['serversource'].replace('.jpg', '') +
                    '_temp' + ext) as im:
                width, height = im.size
            diff = int(image['width']) - width
            if diff != 0:
                diff = diff/2
        else:
            diff = 0
            width = int(image['width'])
            height = int(image['height'])
        c = canvas.Canvas(
            work_dir + 'tempimage' + str(counter) + '.pdf')
        c.drawImage(image['serversource'],
                    int(image['bbox'].split(',')[0].split('.')[0]) + diff,
                    int(image['bbox'].split(',')[1].split('.')[0]),
                    width=int(width),
                    height=int(height),
                    mask='auto')
        c.save()
        temp_imgs.append(work_dir + 'tempimage' +
                         str(counter) + '.pdf')
        counter += 1
    counter = 1
    for tempimg in temp_imgs:
        imagepdf = PdfFileReader(open(tempimg, 'rb'))
        output_file = PdfFileWriter()
        input_file = PdfFileReader(open(currentpdf, "rb"))
        page_count = input_file.getNumPages()
        for page_number in range(page_count):
            input_page = input_file.getPage(page_number)
            input_page.mergePage(imagepdf.getPage(0))
            output_file.addPage(input_page)
        with open(
                os.path.join(work_dir, 'temp' + str(counter) + '.pdf'),
                "wb") as outputStream:
            output_file.write(outputStream)
            completed_temps.append(
                os.path.join(work_dir, 'temp' + str(counter) + '.pdf'))
        currentpdf = work_dir + 'temp' + str(counter) + '.pdf'
        counter += 1

    if len(completed_temps) > 0:
        print completed_temps
        print
        print pdf_with_images
        os.rename(completed_temps[
                  len(completed_temps) - 1], pdf_with_images)
    else:
        shutil.copyfile(currentpdf, pdf_with_images)


def draw_visualization_on_pdf(
        vizs,
        currentpdf,
        pdf_with_vizs,
        work_dir):
    counter = 1
    first = True
    for viz in vizs:
        if first is False:
            currentpdf = work_dir + 'temp' + \
                str(counter - 1) + '.pdf'
        vizpdf = PdfFileReader(open(viz, "rb"))
        output_file = PdfFileWriter()
        input_file = PdfFileReader(open(currentpdf, "rb"))
        page_count = input_file.getNumPages()
        for page_number in range(page_count):
            input_page = input_file.getPage(page_number)
            input_page.mergePage(vizpdf.getPage(0))
            output_file.addPage(input_page)
        if counter == len(vizs):
            with open(pdf_with_vizs, "wb") as outputStream:
                output_file.write(outputStream)
        else:
            with open(
                    work_dir + 'temp' + str(counter) + '.pdf',
                    "wb") as outputStream:
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


def map_variables(var_list, data):
    value_list = []
    for i, var in enumerate(var_list):
        if var is None:
            value_list.append(None)
        else:
            var_parts = var.split('.')
            data_chunk = data
            for i2, var_part in enumerate(var_parts):
                try:
                    if var_part in data_chunk:
                        new_chunk = data_chunk[var_part]
                        data_chunk = new_chunk
                        if i2 == len(var_parts) - 1:
                            value_list.append(data_chunk)
                    else:
                        value_list.append(None)
                        continue
                except TypeError:
                    value_list.append(None)
                    continue

    return value_list


def build_visualization(server_data):
    VIZdata = []
    for i, data in enumerate(server_data):
        row = []
        row.append(data)
        for j, specific in enumerate(data):
            row.append(specific)
        VIZdata.append(row)

    return VIZdata


def translate_placeholders(image_info, server_data, work_dir, page_count):
    organized_image_info = {}
    server_images = []
    DTdimensions = []
    DTcoords = []
    SLdimensions = []
    SLcoords = []
    for image in image_info:
        img_spec = image
        if img_spec['tag'] == 'DataTable':
            DTdimensions = [int(img_spec['width']),
                            int(img_spec['height'])]
            x = img_spec['bbox'].split(",")[0].split('.')[0]
            y = img_spec['bbox'].split(",")[1].split('.')[0]
            DTcoords = [int(x), int(y)]
        elif img_spec['tag'] == 'SparkLine':
            SLdimensions = [int(img_spec['width']),
                            int(img_spec['height'])]
            x = img_spec['bbox'].split(",")[0].split('.')[0]
            y = img_spec['bbox'].split(",")[1].split('.')[0]
            SLcoords = [int(x), int(y)]
        else:
            value = map_variables([img_spec['tag']], server_data)
            if value[0] is not None:
                
                ext = '.' + \
                    value[0].split(".")[-1]
                if ext not in ['jpg', 'png', 'gif']:
                    ext = 'jpg'
                print "ext: " + ext
                try:
                    remote_file = requests.get(value[0])
                    with open(
                        os.path.join(
                            work_dir,
                            'temp',
                            img_spec['tag'] + page_count + ext
                        ),'wb') as local_file:
                        local_file.write(remote_file.content)
                    img_spec['serversource'] = os.path.join(
                        work_dir,
                        'temp',
                        img_spec['tag'] + page_count + ext)
                except Exception as e:
                    print "can't download " + str(value[0]) + str(e)
                    img_spec['serversource'] = 'placeholders/sample.jpg'
                server_images.append(img_spec)
    organized_image_info = {
        'DTdimensions': DTdimensions,
        'DTcoords': DTcoords,
        'SLdimensions': SLdimensions,
        'SLcoords': SLcoords,
        'ServerImages': server_images
    }
    return organized_image_info
