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

def get_image_tag(filename):
    try:
        exif_dict = piexif.load(filename)
        if piexif.ExifIFD.UserComment in exif_dict['Exif']:
            message = exif_dict['Exif'][piexif.ExifIFD.UserComment].strip(' \t\r\n\0')
        else:
            message = ''
    except Exception as e:
        message = "no tag or issue finding tag"
    return message
