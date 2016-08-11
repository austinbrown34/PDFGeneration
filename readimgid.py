from gi.repository.GExiv2 import Metadata

m = Metadata()

m.open_path('pdfdata/Im3.jpg')

# print m.get_exif_tags()
# key = 'Exif.Photo.UserComment'
# value = 'weed'
# m.set_tag_string(key, value)
# m.save_file('weed.jpg')

print m.get_tag_string('Exif.Photo.UserComment')
