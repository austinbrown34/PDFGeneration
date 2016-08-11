import sys

pdf = file(sys.argv[1], "rb").read()

startmark = "\xff\xd8"
startfix = 0
endmark = "\xff\xd9"
endfix = 2
i = 0
jpg_ranges = []
njpg = 0
newpdf = file("newpdf.pdf", "wb")
while True:
    istream = pdf.find("stream", i)
    if istream < 0:
        break
    istart = pdf.find(startmark, istream, istream+20)
    if istart < 0:
        i = istream+20
        continue
    iend = pdf.find("endstream", istart)
    if iend < 0:
        raise Exception("Didn't find end of stream!")
    iend = pdf.find(endmark, iend-20)
    if iend < 0:
        raise Exception("Didn't find end of JPG!")

    istart += startfix
    iend += endfix
    print "JPG %d from %d to %d" % (njpg, istart, iend)
    jpg_ranges.append([njpg, istart, iend])
    jpg = pdf[istart:iend]

    jpgfile = file("jpg%d.jpg" % njpg, "wb")
    jpgfile.write(jpg)
    jpgfile.close()
    njpg += 1
    i = iend

placeholder = 0
for jpg_item in jpg_ranges:
    range_start = jpg_item[1]
    range_end = jpg_item[2]
    newpdf.write(pdf[placeholder:range_start])
    counter = range_start
    while counter < range_end + 1:
        empty_bytes = bytes(1)
        newpdf.write(empty_bytes)
        counter += 1
    placeholder = range_end + 1
newpdf.write(pdf[placeholder:sys.getsizeof(pdf)])
newpdf.close()
newpdf = file('newpdf.pdf', "rb").read()
print sys.getsizeof(pdf)
print sys.getsizeof(newpdf)
