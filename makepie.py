from random import *

data = [["\u03b1-Pinene", 13.0, 83.0], ["Camphene", 10.0, 83.0], ["Fenchone", 5.0, 83.0], ["Terpinolene", 5.0, 83.0], ["\u03b1-Terpinene", 5.0, 83.0], ["Isopulegol", 4.0, 83.0], ["\u03b1-Phellandrene", 4.0, 83.0], ["p-Cymene", 4.0, 83.0], ["Sabinene", 3.0, 83.0], ["Endo-Fenchyl Alcohol", 3.0, 83.0], ["Caryophyllene Oxide", 3.0, 83.0], ["\u03b1-Terpineol", 3.0, 83.0], ["Borneol", 3.0, 83.0], ["\u03b2-Pinene", 2.0, 83.0], ["Isoborneol", 2.0, 83.0], ["Menthol", 2.0, 83.0], ["\u03b2-Myrcene", 2.0, 83.0], ["3-Carene", 2.0, 83.0], ["Geranyl Acetate", 2.0, 83.0], ["Linalool", 2.0, 83.0], ["Cedrol", 2.0, 83.0], ["Eucalyptol", 2.0, 83.0], ["Pulegone", 2.0, 83.0], ["Geraniol", 2.0, 83.0], ["\u03b1-Bisabolol", 2.0, 83.0], ["\u03b2-Caryophyllene", 0.0, 83.0], ["Valencene", 0.0, 83.0], ["\u03b1-Cedrene", 0.0, 83.0], ["\u03b1-Humulene", 0.0, 83.0], ["Ocimene", 0.0, 83.0], ["cis-Nerolidol", 0.0, 83.0], ["trans-Nerolidol", 0.0, 83.0], ["\u03b4-Limonene", 0.0, 83.0], ["Guaiol", 0.0, 83.0]]

# {
#   "label": "JavaScript",
#   "value": 264131,
#   "color": "#2484c1"
# }


def get_colors(how_many):
    colors = []
    h, s, v = random() * 6, .5, 243.2
    for i in range(how_many):
        h += 3.708
        color = '#' + '%02x' * 3 % ((v, v - v * s * abs(1 - h % 2), v - v * s) * 3)[5 ** int(h)/3 % 3::int(h) % 2 + 1][:3]
        colors.append(color)
        if i % 5/4:
            s += .1
            v -= 51.2
    return colors


def make_pie_data(data, color_list):
    new_data = []
    for i, e in enumerate(data):
        pie_obj = {
            'label': e[0],
            'value': e[1],
            'color': color_list[i]
        }
        new_data.append(pie_obj)
    return new_data


color_list = get_colors(len(data))



new_data = make_pie_data(data, color_list)


print new_data
