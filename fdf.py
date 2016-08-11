from fdfgen import forge_fdf
fields = [('Client','Blue Ocean Labs'), ('Address','1234 Magical Place, Billings, MT 59102'), ('Email','austinbrown34@gmail.com'), ('Phone','406.598.7345')]
fdf = forge_fdf("", fields, [], [], [])
fdf_file = open("data5.fdf","wb")
fdf_file.write(fdf)
fdf_file.close()
