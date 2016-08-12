from PIL import Image
import piexif

exif_dict = piexif.load("LabLogo.jpg")

if piexif.ExifIFD.UserComment in exif_dict['Exif']:
    print exif_dict['Exif'][piexif.ExifIFD.UserComment]
# thumbnail = exif_dict.pop("thumbnail")
# if thumbnail is not None:
#     with open("thumbnail.jpg", "wb+") as f:
#         f.write(thumbnail)
# for ifd_name in exif_dict:
#     print("\n{0} IFD:".format(ifd_name))
#     for key in exif_dict[ifd_name]:
#         try:
#             print(key, exif_dict[ifd_name][key][:10])
#         except:
#             print(key, exif_dict[ifd_name][key])

# exif_ifd = {
#             piexif.ExifIFD.UserComment: u"DataTable"
#             }
#
#
# exif_dict = {"Exif":exif_ifd}
# exif_bytes = piexif.dump(exif_dict)
# im = Image.open("LabLogo.jpg")
# im.save("LabLogo.jpg", exif=exif_bytes)

# exif_dict = piexif.load("LabLogo.jpg")
# print exif_dict['Exif']
# for ifd_name in exif_dict:
#     print("\n{0} IFD:".format(ifd_name))
#     for key in exif_dict[ifd_name]:
#         try:
#             print(key, exif_dict[ifd_name][key][:10])
#         except:
#             print(key, exif_dict[ifd_name][key])
