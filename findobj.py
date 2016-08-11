import sys
import os

from pdfrw import PdfReader, PdfWriter
from pdfrw.findobjs import page_per_xobj


inpfn, = sys.argv[1:]
outfn = 'extract.' + os.path.basename(inpfn)
pages = list(page_per_xobj(PdfReader(inpfn).pages, margin=0.5*72))
if not pages:
    raise IndexError("No XObjects found")
writer = PdfWriter()
writer.addpages(pages)
writer.write(outfn)
