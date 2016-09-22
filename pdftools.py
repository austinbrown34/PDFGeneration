#_*_ coding: utf-8 _*_
# python 2
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
from pdfservices import ImageExtractorService
import urllib2
import shutil
import requests
import json

os.environ['PATH'] = os.environ['PATH'] + ':' + os.environ['LAMBDA_TASK_ROOT'] + '/bin'
os.environ['LD_LIBRARY_PATH'] = os.environ['LAMBDA_TASK_ROOT'] + '/bin'
# os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH'] + ':' + '/tmp/fontconfig/usr/lib'
os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH'] + ':' + os.environ['LAMBDA_TASK_ROOT'] + '/fontconfig/usr/lib'

def get_fonts():
    args = ['fc-list']
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    out, err = process.communicate()
    print(out)

def test_binaries():
    args = ['pdftk', '--version']
    args2 = ['phantomjs', '--help']
    subprocess.call(args)
    subprocess.call(args2)

def get_acroform_fields_pdftk(filename):
    print filename
    args = ['pdftk', filename, 'dump_data_fields', 'output', '/tmp/work/dump_data_fields.txt']

    try:
        print "setup pdftk ran"
        subprocess.call(args)
    except Exception as e:
        print str(e)
        print "made it to the exception for pdftk"
    field_names = []
    with open('/tmp/work/dump_data_fields.txt') as ddf:
        for i, line in enumerate(ddf):
            if 'FieldName:' in line:
                field_names.append(line.split('FieldName: ')[1].strip())
    print "field names:"
    print field_names
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
            print "printing tag:"
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
        coordinates,
        report_units,
        secondary_report_units):
    with open(data_vis_name, 'r') as file:
        content = file.readlines()
    print "read the js file"
    print data_vis_name
    content[1] = json.dumps(data) + ';\n'
    content[3] = str(dimensions) + ';\n'
    content[5] = str(coordinates) + ';\n'
    content[10] = '"' + str(report_units) + '"' + ';\n'
    content[12] = '"' + str(secondary_report_units) + '"' + ';\n'
    data_vis_name_split = data_vis_name.split("/")
    data_vis_name_split.pop()
    data_vis_location = '/tmp/'
    for i, e in enumerate(data_vis_name_split):
        data_vis_location += e + '/'
        if not os.path.isdir(data_vis_location):
            os.makedirs(data_vis_location)
    with open(os.path.join('/tmp', data_vis_name), 'w') as file:
        file.writelines(content)
    print "wrote the js file"
    with open(os.path.join('/tmp', data_vis_name), 'r') as file:
        content = file.readlines()
    print content

def generate_visualizations(viz_files, controljs, out_dir, vizpdfs=None):
    for i, viz in enumerate(viz_files):
        print "from generate viz - viz, controljs, out_dir"
        print viz
        print controljs
        print out_dir
        try:
            pdfout = out_dir + viz.split('/')[-1].replace('.html', '.pdf')
            if vizpdfs is not None:
                pdfout = out_dir + vizpdfs[i].split('/')[-1]

            call = [
                'phantomjs',
                controljs,
                viz,
                pdfout
            ]
            subprocess.call(call)
            temp_dirs = os.listdir(out_dir)
            print "out_dir"
            print str(temp_dirs)
        except Exception as e:
            print str(e)
            print "exception for phantomjs"


def generate_visualization(viz_file, controljs, out_dir, vizpdf):
    print "from generate viz - viz, controljs, out_dir"
    print viz_file
    print controljs
    print out_dir
    try:
        # pdfout = out_dir + viz_file.split('/')[-1].replace('.html', '.pdf')

        pdfout = out_dir + vizpdf.split('/')[-1]

        call = [
            'phantomjs',
            controljs,
            viz_file,
            pdfout
        ]
        subprocess.call(call)
        temp_dirs = os.listdir(out_dir)
        print "out_dir"
        print str(temp_dirs)
    except Exception as e:
        print str(e)
        print "exception for phantomjs"


def draw_images_on_pdf(
        images,
        currentpdf,
        pdf_with_images,
        work_dir):
    counter = 1
    temp_imgs, completed_temps = [], []
    for image in images:
        ext = '.' + image['serversource'].split('.')[-1]
        # if ext == ".jpg":
        print "opening serversource img"
        im = IMG.open(image['serversource'])
        size = int(image['width']), int(image['height'])
        im.thumbnail(size, IMG.ANTIALIAS)
        im.save(os.path.join(work_dir, image['serversource'].replace(ext, '') +
                '_temp' + ext))
        print "saving thumbnail @ " + os.path.join(work_dir, image['serversource'].replace(ext, '') +
                '_temp' + ext)
        # image['serversource'] = os.path.join(work_dir, image['serversource'].replace(ext, '') +
        #         '_temp' + ext)
        # print "setting serversource"
        with IMG.open(os.path.join(work_dir, image['serversource'].replace(ext, '') + '_temp' + ext)) as im:
            width, height = im.size
        print "opened the new serversource to set width and height -> " + image['serversource']
        diff = int(image['width']) - width
        if diff != 0:
            diff = diff/2
        diff2 = int(image['height']) - height
        if diff2 != 0:
            diff2 = diff2/2

        # else:
        #     diff = 0
        # width = int(image['width'])
        # height = int(image['height'])

        c = canvas.Canvas(
            work_dir + 'tempimage' + str(counter) + '.pdf')
        c.drawImage(image['serversource'],
                    int(image['bbox'].split(',')[0].split('.')[0]) + diff,
                    int(image['bbox'].split(',')[1].split('.')[0]) + diff2,
                    width=int(width),
                    height=int(height),
                    mask='auto')
        c.save()
        print "drew canvas image"
        temp_imgs.append(work_dir + 'tempimage' +
                         str(counter) + '.pdf')
        counter += 1
    counter = 1
    for tempimg in temp_imgs:
        print "printing tempimg"
        print tempimg
        try:
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
            currentpdf = os.path.join(work_dir, 'temp' + str(counter) + '.pdf')
            counter += 1
        except Exception as e:
            print str(e)
            print "made it to the draw_images_on_pdf exception"
            pass

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
    try:
        for viz in vizs:
            print "working on " + str(viz)
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
                with open(work_dir + 'temp' + str(counter) + '.pdf',"wb") as outputStream:
                    output_file.write(outputStream)
            counter += 1
            first = False
    except Exception as e:
        print str(e)
        print "exception for drawing viz"


def merge_all_pages(pages, final):
    call = [
        'pdftk'
    ]
    for page in pages:
        call.append(page)
    call.append('cat')
    call.append('output')
    call.append(final)
    print "this is the call"
    print call
    try:
        subprocess.call(call)
    except Exception as e:
        print "made it to the merge_all_pages exception"
        print str(e)



def map_variables(var_list, data):
    value_list = []
    p_o_p = 0
    print "checking out page_of_pages for issues"
    for i, var in enumerate(var_list):
        print "this is the var:"
        print var
        if var == 'page_of_pages':
            print "on page_of_pages"
            p_o_p = 1
        else:
            p_o_p = 0
        if var is None:
            print "var is none so appending blank "
            value_list.append('')
        else:
            var = var.replace('::', '.')
            var_parts = var.split('.')
            print "these are the var parts:"
            print str(var_parts)
            if p_o_p == 1:
                print "var_parts"
                print var_parts
            data_chunk = data
            for i2, var_part in enumerate(var_parts):
                try:
                    if var_part in data_chunk:
                        if p_o_p == 1:
                            print "var_part"
                            print var_part
                            print "this is in data_chunk"
                        new_chunk = data_chunk[var_part]
                        data_chunk = new_chunk
                        if i2 == len(var_parts) - 1:
                            if data_chunk in [{},[],'null',()] or data_chunk is None:
                                print "value was empty or null or none - setting value to blank"
                                data_chunk = ''
                            value_list.append(data_chunk)
                    else:
                        print "var part not in server data - adding blank"
                        value_list.append('')
                        break
                except TypeError:
                    print "There was a type error... adding blank"
                    value_list.append('')
                    break
    print "this is the value list:"
    print value_list
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

def split_viz_into_parts(viz_data, split_code):
    new_viz_data = []
    viz_length = len(viz_data)
    num_of_parts = int(split_code.split('/')[1])
    chunk_pos = int(split_code.split('/')[0])
    viz_chunk = int(viz_length / num_of_parts)
    start = (viz_chunk * (chunk_pos - 1))
    if chunk_pos == num_of_parts:
        for x in range(start, len(viz_data)):
            new_viz_data.append(viz_data[x])
    else:
        for x in range(start, (start + viz_chunk)):
            new_viz_data.append(viz_data[x])

    return new_viz_data

def translate_placeholders(image_info, server_data, work_dir, page_count):
    visualizations = []
    organized_image_info = {}
    server_images = []
    split_code = None

    for image in image_info:
        with_spark = False
        img_spec = image
        print "tag:"
        print img_spec['tag']
        if img_spec['tag'] is None:
            continue
        if img_spec['tag'].startswith('viz_'):
            print "tag starts with viz_"
            viz_pieces = img_spec['tag'].split('_')
            if img_spec['tag'].endswith('_split'):
                split_code = viz_pieces[len(viz_pieces) - 2]
                viz_pieces = viz_pieces[:-2]
            if img_spec['tag'].endswith('_with_sparkline'):
                # split_code = viz_pieces[len(viz_pieces) - 2]
                with_spark = True
                viz_pieces = viz_pieces[:-2]
            if len(viz_pieces) == 3:
                print "tag has 3 pieces"
                viz_folder = viz_pieces[0]
                print "viz_folder:"
                print viz_folder
                viz_type = viz_pieces[1]
                print "viz_type:"
                print viz_type
                viz_specific = viz_pieces[1] + '_' + viz_pieces[2]
                print "viz_specific:"
                print viz_specific
                viz_file = viz_specific + '.html'
                if with_spark:
                    viz_file = viz_specific + '_with_sparkline.html'
                print "viz_file:"
                print viz_file
                viz_dimensions = [int(img_spec['width']),
                                int(img_spec['height'])]
                print "viz_dimensions:"
                print viz_dimensions
                x = img_spec['bbox'].split(",")[0].split('.')[0]
                print "x:"
                print x
                y = img_spec['bbox'].split(",")[1].split('.')[0]
                print "y:"
                print y
                viz_coords = [int(x), int(y)]
                print "viz_coords:"
                print viz_coords
                # print "serverdata['viz']:"
                # print server_data['viz']
                try:
                    viz_data = server_data['viz'][viz_specific]
                    if with_spark:
                        viz_data = server_data['viz'][viz_specific + '_with_sparkline']
                    print "viz_data:"

                    if split_code is not None:
                        viz_data = split_viz_into_parts(viz_data, split_code)
                    print viz_data
                    visualizations.append({
                        'viz_folder': viz_folder,
                        'viz_type': viz_type,
                        'viz_specific': viz_specific,
                        'viz_file': viz_file,
                        'viz_dimensions': viz_dimensions,
                        'viz_coords': viz_coords,
                        'viz_data': viz_data
                    })
                    print "appended to visualizations"
                except Exception as e:
                    print "issue with a viz"
                    print str(e)
                    continue
        else:
            value = map_variables([img_spec['tag']], server_data)
            print "this is the value"
            print value
            if value[0] is not None and value[0] != '':
                try:
                    print "image value is:"
                    print value[0]
                    ext = '.' + value[0].split(".")[-1]
                    if ext not in ['.jpg', '.png', '.gif']:
                        ext = '.jpg'
                    print "ext: " + ext
                    remote_file = requests.get(value[0])
                    with open(
                        os.path.join(
                            work_dir,
                            'temp',
                            img_spec['tag'] + page_count + ext
                        ), 'wb') as local_file:
                        local_file.write(remote_file.content)
                    print "wrote local file"
                    img_spec['serversource'] = os.path.join(
                        work_dir,
                        'temp',
                        img_spec['tag'] + page_count + ext)
                    print "serversource is:"
                    print img_spec['serversource']
                except Exception as e:
                    print "can't download " + str(value[0]) + str(e)
                    if not os.path.isdir('/tmp/work'):
                        os.makedirs('/tmp/work')
                    if not os.path.isdir('/tmp/work/temp'):
                        os.makedirs('/tmp/work/temp')
                    if not os.path.isdir('/tmp/work/temp/placeholders'):
                        os.makedirs('/tmp/work/temp/placeholders')
                    shutil.copyfile(
                        os.path.join(
                            'placeholders',
                            'sample.jpg'
                        ), os.path.join(
                            work_dir,
                            'temp',
                            'placeholders',
                            'sample.jpg'
                        )
                    )

                    img_spec['serversource'] = 'placeholders/sample.jpg'
                    pass
            else:
                print "value is None"
                if not os.path.isdir('/tmp/work'):
                    os.makedirs('/tmp/work')
                if not os.path.isdir('/tmp/work/temp'):
                    os.makedirs('/tmp/work/temp')
                if not os.path.isdir('/tmp/work/temp/placeholders'):
                    os.makedirs('/tmp/work/temp/placeholders')
                img_spec['serversource'] = 'placeholders/sample.jpg'

                shutil.copyfile(
                    os.path.join(
                        'placeholders',
                        'sample.jpg'
                    ), os.path.join(
                        work_dir,
                        'temp',
                        'placeholders',
                        'sample.jpg'
                    )
                )
            server_images.append(img_spec)
    organized_image_info = {
        'Visualizations': visualizations,
        'ServerImages': server_images
    }
    print "returning from translate_placeholders"
    return organized_image_info
