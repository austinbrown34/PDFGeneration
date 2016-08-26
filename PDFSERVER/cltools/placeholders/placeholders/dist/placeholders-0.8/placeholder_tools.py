import os
import sys
import piexif
from PIL import Image as IMG


def set_image_tag(filename, tag):
    exif_ifd = {
        piexif.ExifIFD.UserComment: unicode(tag)
    }
    exif_dict = {"Exif": exif_ifd}
    exif_bytes = piexif.dump(exif_dict)
    im = IMG.open(filename)
    im.save(filename, exif=exif_bytes)
