#!/usr/bin/env python
import sys
import os
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter
import lxml.etree
image_info = []
pagenos = set()
maxpages = 0
password = ''
caching = True
debug = 0
rotation = 0
stripcontrol = False
layoutmode = 'normal'
pageno = 1
scale = 1
fname = 'datatest.pdf'
PDFDocument.debug = debug
PDFParser.debug = debug
CMapDB.debug = debug
PDFPageInterpreter.debug = debug
rsrcmgr = PDFResourceManager(caching=caching)
outputdir = 'pdfdata'
outfile = os.path.join(outputdir,'underthehood.xml')
outfp = file(outfile, 'w')
codec = 'utf-8'
laparams = LAParams()
imagewriter = ImageWriter(outputdir)
device = XMLConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
                      imagewriter=imagewriter)
interpreter = PDFPageInterpreter(rsrcmgr, device)

fp = file(fname, 'rb')
interpreter = PDFPageInterpreter(rsrcmgr, device)

for page in PDFPage.get_pages(fp, pagenos,
                              maxpages=maxpages, password=password,
                              caching=caching, check_extractable=True):
    page.rotate = (page.rotate+rotation) % 360
    interpreter.process_page(page)
fp.close()
device.close()
outfp.close()

root = lxml.etree.parse(outfile)
found_images = root.findall('.//image')
found_image_boxes = root.xpath('.//figure[image]')
for i, e in enumerate(found_images):
    image_info.append({"src" : e.attrib['src'], "height" : e.attrib['height'], "width" : e.attrib['width'], "bbox" : found_image_boxes[i].attrib['bbox']})

print image_info
