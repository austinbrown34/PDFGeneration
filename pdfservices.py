from pdfminer.pdftypes import LITERALS_DCT_DECODE
from pdfminer.pdfcolor import LITERAL_DEVICE_GRAY
from pdfminer.pdfcolor import LITERAL_DEVICE_RGB
import boto3
import os
import yaml
from shutil import copyfile
import requests
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TemplateService(object):
    def __init__(self, directory):
        self.directory = directory

    def download_config(self, config_folder, config, destination):
        copyfile(os.path.join(self.directory, config_folder, config), destination)

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
        # print "this is the yaml obj:"
        # print str(cfg_obj)
        # print "these are our template keys:"
        # print str(template_keys)
        logo = cfg_obj['template_logo']
        lab = logo.split('assets/img/labs/')[1].split('/')[0]
        temp_templates = []
        template_rules = cfg_obj['template_rules']
        unmatched = []
        for i, rule in enumerate(template_rules):
            matched = False
            # print "rule:"
            # print rule
            for j, template_key in enumerate(template_keys):
                # template_key[0] = unicode(template_key[0], 'utf-8')
                try:
                    template_key[0] = template_key[0].replace(u'\u2013', '-')
                except Exception as e:
                    # print str(e)
                    pass
                    # template_key[1] = unicode(template_key[1], 'utf-8')
                try:
                    template_key[1] = template_key[1].replace(u'\u2013', '-')
                except Exception as e:
                    # print str(e)
                    pass
                # print "template_key"
                # print template_key
                if rule['rule']['package_key'] is not None:
                    if template_key[0] == rule['rule']['package_key']:
                        temp_templates.append(rule['rule']['included_templates'])
                        matched = True
                else:
                    if template_key[1] == rule['rule']['package_name']:
                        temp_templates.append(rule['rule']['included_templates'])
                        matched = True
                if not matched:
                    unmatched.append({
                        'template_key': template_key[0],
                        'template_name': template_key[1],
                    })

        message = 'The following packages for ' + lab + ' are missing templates: \n\n'
        for i, e in enumerate(unmatched):
            message += 'PKG NAME: ' + str(e['template_name']) + '\nPKG KEY: ' + str(e['template_key']) + '\n\n'

        # requests.post(
        #     'https://hooks.slack.com/services/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',
        #     data={
        #         'payload': json.dumps({'text': message})
        #         }
        #     )
        if len(unmatched) > 0:
            print "--------------------------------------"
            print bcolors.FAIL + message + bcolors.ENDC
            print "--------------------------------------"
        # print message
        template_list_builder(temp_templates)
        return templates

    def get_logo(self, config):
        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        logo = cfg_obj['template_logo']
        return logo

    def get_scripts(self, config):
        scripts = []
        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        # print str(cfg_obj)
        if cfg_obj is not None:
            template_scripts = cfg_obj['template_scripts']
        if template_scripts is None:
            scripts = []
        else:
            for script in template_scripts:
                scripts.append(script)
        return scripts

    def download_templates(self, template_folder, templates):
        for template in templates:
            copyfile(
                os.path.join(
                    self.directory,
                    template_folder,
                    template
                    ),
                os.path.join(
                    '/tmp',
                    'work',
                    template
                    )
                )

    def download_scripts(self, template_folder, scripts):
        for script in scripts:
            copyfile(
                os.path.join(
                    self.directory,
                    template_folder,
                    script
                    ),
                os.path.join(
                    '/tmp',
                    'work',
                    script
                    )
                )
        print "Downloaded Scripts..."


class S3TemplateService(object):

    def __init__(self, credentials=None, bucket=None):
        if credentials is None:
            self.credentials = None
        else:
            self.credentials = credentials
        if bucket is None:
            return
        self.bucket = bucket
        if self.credentials is not None:
            self.session = boto3.Session(
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key']
            )
        else:
            self.session = boto3.Session()
        self.s3 = self.session.resource('s3')
        self.s3_client = self.session.client('s3')

    def download_config(self, config_folder, config, destination):
        def lambda_handler(event, context):
            # print "made it to the lambda handler"
            bucket_name = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            if not key.endswith('/'):
                try:
                    split_key = key.split('/')
                    file_name = split_key[-1]
                    s3templates.s3.meta.client.download_file(
                        bucket_name,
                        key,
                        '/tmp/work/config.yaml'
                        )
                except Exception as e:
                    print "--------------------------------------"
                    print bcolors.FAIL + "Download Config Lambda Handler Exception" + bcolors.ENDC
                    print str(e)
                    print "--------------------------------------"
            return (bucket_name, key)
        try:
            self.s3.meta.client.download_file(
                self.bucket,
                os.path.join(config_folder, config),
                destination
                )
        except Exception as e:
            # print str(e)
            print "--------------------------------------"
            print bcolors.FAIL + "Download Config Exception" + bcolors.ENDC
            print "--------------------------------------"
            # print "showing contents of tmp"
            # os.listdir('/tmp/')

    def get_templates(self, config, template_folder, template_keys):
        templates = []
        # print "getting templates"
        def template_list_builder(temp_templates):
            for temp in temp_templates:
                if not isinstance(temp, (str, unicode)):
                    template_list_builder(temp)
                    continue
                templates.append(temp)

        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        # print "this is the yaml obj:"
        # print str(cfg_obj)
        # print "these are our template keys:"
        # print str(template_keys)
        temp_templates = []
        template_rules = cfg_obj['template_rules']
        logo = cfg_obj['template_logo']
        lab = logo.split('assets/img/labs/')[1].split('/')[0]
        unmatched = []
        for i, rule in enumerate(template_rules):
            matched = False
            # print "rule:"
            # print rule
            for j, template_key in enumerate(template_keys):
                # template_key[0] = unicode(template_key[0], 'utf-8')
                try:
                    template_key[0] = template_key[0].replace(u'\u2013', '-')
                except Exception as e:
                    # print str(e)
                    pass
                    # template_key[1] = unicode(template_key[1], 'utf-8')
                try:
                    template_key[1] = template_key[1].replace(u'\u2013', '-')
                except Exception as e:
                    # print str(e)
                    pass
                # print "template_key"
                # print template_key
                if rule['rule']['package_key'] is not None:
                    if template_key[0] == rule['rule']['package_key']:
                        temp_templates.append(rule['rule']['included_templates'])
                        matched = True
                else:
                    if template_key[1] == rule['rule']['package_name']:
                        temp_templates.append(rule['rule']['included_templates'])
                        matched = True
                if not matched:
                    unmatched.append({
                        'template_key': template_key[0],
                        'template_name': template_key[1],
                    })
        message = 'The following packages for ' + lab + ' are missing templates: \n\n'
        for i, e in enumerate(unmatched):
            message += 'PKG NAME: ' + str(e['template_name']) + '\nPKG KEY: ' + str(e['template_key']) + '\n\n'
        if len(unmatched) > 0:
            print "--------------------------------------"
            print bcolors.FAIL + message + bcolors.ENDC
            print "--------------------------------------"
        requests.post(
            'https://hooks.slack.com/services/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',
            data={
                'payload': json.dumps({'text': message})
                }
            )
        template_list_builder(temp_templates)
        return templates

    def get_logo(self, config):
        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        logo = cfg_obj['template_logo']
        return logo
    def get_scripts(self, config):
        scripts = []
        cfg = open(config)
        cfg_obj = yaml.safe_load(cfg)
        cfg.close()
        # print str(cfg_obj)
	if cfg_obj is not None:
	    template_scripts = cfg_obj['template_scripts']
            if template_scripts is None:
                scripts = []
	    else:
                for script in template_scripts:
                    scripts.append(script)
        return scripts

    def download_templates(self, template_folder, templates):
        for template in templates:
            def lambda_handler(event, context):
                # print "made it to the lambda handler"
                bucket_name = event['Records'][0]['s3']['bucket']['name']
                key = event['Records'][0]['s3']['object']['key']
                if not key.endswith('/'):
                    try:
                        split_key = key.split('/')
                        file_name = split_key[-1]
                        s3templates.s3.meta.client.download_file(
                            bucket_name,
                            key,
                            '/tmp/work/' + template
                            )
                    except Exception as e:
                        print "--------------------------------------"
                        print bcolors.FAIL + "Download Templates Lambda Handler Exception" + bcolors.ENDC
                        print str(e)
                        print "--------------------------------------"
                return (bucket_name, key)
            self.s3.meta.client.download_file(
                self.bucket,
                os.path.join(template_folder, template),
                os.path.join('/tmp', 'work', template)
            )

    def download_scripts(self, template_folder, scripts):
        for script in scripts:
            def lambda_handler(event, context):
                # print "made it to the lambda handler"
                bucket_name = event['Records'][0]['s3']['bucket']['name']
                key = event['Records'][0]['s3']['object']['key']
                if not key.endswith('/'):
                    try:
                        split_key = key.split('/')
                        file_name = split_key[-1]
                        s3templates.s3.meta.client.download_file(
                            bucket_name,
                            key,
                            '/tmp/work/' + script
                            )
                    except Exception as e:
                        print "--------------------------------------"
                        print bcolors.FAIL + "Download Scripts Lambda Handler Exception" + bcolors.ENDC
                        print str(e)
                        print "--------------------------------------"
                return (bucket_name, key)
            self.s3.meta.client.download_file(
                self.bucket,
                os.path.join(template_folder, script),
                os.path.join('/tmp', 'work', script)
            )
        print "Downloaded Scripts..."
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
