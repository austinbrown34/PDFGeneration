from pdfminer.pdftypes import LITERALS_DCT_DECODE
from pdfminer.pdfcolor import LITERAL_DEVICE_GRAY
from pdfminer.pdfcolor import LITERAL_DEVICE_RGB
import boto3
import os
import yaml


class S3TemplateService(object):

    def __init__(self, credentials, bucket):
        self.credentials = credentials
        self.bucket = bucket
        self.session = boto3.Session(
            aws_access_key_id=credentials['aws_access_key_id'],
            aws_secret_access_key=credentials['aws_secret_access_key']
        )
        self.s3 = self.session.resource('s3')
        self.s3_client = self.session.client('s3')

    def download_config(self, config_folder, config, destination):
        self.s3.meta.client.download_file(
            self.bucket,
            os.path.join(config_folder, config),
            destination
        )

    def get_templates(self, config, template_folder, template_keys):
        templates = []

        def template_list_builder(temp_templates):
            for temp in temp_templates:
                if not isinstance(temp, (str, unicode)):
                    template_list_builder(temp)
                    continue
                templates.append(temp)

        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        temp_templates = []
        template_rules = cfg_obj['template_rules']
        for template_key in template_keys:
            if template_key in template_rules:
                temp_templates.append(template_rules[template_key])

        template_list_builder(temp_templates)
        return templates

    def get_scripts(self, config):
        scripts = []
        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        template_scripts = cfg_obj['template_scripts']
        for script in template_scripts:
            scripts.append(script)
        return scripts

    def download_templates(self, template_folder, templates):
        for template in templates:
            self.s3.meta.client.download_file(
                self.bucket,
                os.path.join(template_folder, template),
                os.path.join('work', template)
            )

    def download_scripts(self, template_folder, scripts):
        for script in scripts:
            self.s3.meta.client.download_file(
                self.bucket,
                os.path.join(template_folder, script),
                os.path.join('work', script)
            )

    def get_presigned_url(self, pdf):
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.Bucket,
                'Key': pdf
            }
        )
        return presigned_url


class ImageExtractorService(object):

    def __init__(self, outdir):
        self.outdir = outdir
        self.jpgs = []
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        return

    def get_jpgs(self):
        return self.jpgs

    def export_image(self, image):
        stream = image.stream
        filters = stream.get_filters()
        (width, height) = image.srcsize
        if len(filters) == 1 and filters[0] in LITERALS_DCT_DECODE:
            ext = '.jpg'
            name = image.name + ext
            path = os.path.join(self.outdir, name)
            fp = file(path, 'wb')
            raw_data = stream.get_rawdata()
            fp.write(raw_data)
            fp.close()
            self.jpgs.append(image.name + ext)
        elif (image.bits == 1 or
              image.bits == 8 and
              image.colorspace in (LITERAL_DEVICE_RGB, LITERAL_DEVICE_GRAY)):
            ext = '.%dx%d.bmp' % (width, height)
        else:
            ext = '.%d.%dx%d.img' % (image.bits, width, height)
        name = image.name + ext
        return name
