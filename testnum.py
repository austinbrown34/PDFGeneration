from decimal import *
import copy


def make_number(data, digits=None, labels=False):
    try:
        new_data = copy.deepcopy(data)
        new_data = float(new_data)
    except ValueError:
        if new_data == "<LOQ":
            new_data = "&ltLOQ"
        if not labels:
            new_data = float(0)

    output = new_data
    if digits is not None and isinstance(new_data, float):
        quantizer = '1.'
        print "digits:"
        print digits
        if int(digits) > 0:
            zeros = '.'
            for i in range(int(digits - 1)):
                zeros += '0'
            quantizer = zeros + '1'
        dec = Decimal(new_data).quantize(Decimal(quantizer))
        print "decimal is: "
        print dec
        output = str(dec)
        # output = float(round(dec, digits))
        print "float is: "
        print output
    if not labels:
        output = float(output)
    return output
