from pdffields import fields as funcs

def main():
    pdf_path = 'datatest.pdf'
    fields = funcs.get_fields(pdf_path)
    fields['Client'] = 'John Smith'
    fields['Address'] = '1234 Waverly Place, Billings, MT 59101'
    fields['Email'] = 'austinbrown34@gmail.com'
    fields['Phone'] = '406.598.7345'
    funcs.write_pdf(pdf_path, fields, 'templatefilledform2.pdf')


if __name__ == '__main__':
    main()
