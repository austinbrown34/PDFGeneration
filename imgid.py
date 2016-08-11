from gi.repository.GExiv2 import Metadata

m = Metadata()

m.open_path('placeholders/sparkline_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'SparkLine'
m.set_tag_string(key, value)
m.save_file('placeholders/sparkline_placeholder.jpg')

m = Metadata()

m.open_path('placeholders/datatable_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'DataTable'
m.set_tag_string(key, value)
m.save_file('placeholders/datatable_placeholder.jpg')

m = Metadata()

m.open_path('placeholders/samplephoto_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'SamplePhoto'
m.set_tag_string(key, value)
m.save_file('placeholders/samplephoto_placeholder.jpg')

m = Metadata()

m.open_path('placeholders/qr_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'QR'
m.set_tag_string(key, value)
m.save_file('placeholders/qr_placeholder.jpg')

m = Metadata()

m.open_path('placeholders/lablogo_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'LabLogo'
m.set_tag_string(key, value)
m.save_file('placeholders/lablogo_placeholder.jpg')

m = Metadata()

m.open_path('placeholders/signature_placeholder.jpg')

print m.get_exif_tags()
key = 'Exif.Photo.UserComment'
value = 'Signature'
m.set_tag_string(key, value)
m.save_file('placeholders/signature_placeholder.jpg')
