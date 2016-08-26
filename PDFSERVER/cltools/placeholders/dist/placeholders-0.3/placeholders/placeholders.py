import os
import sys
import click
import placeholder_tools as pt
import yaml


@click.command()
@click.option('--d', help='The directory where your images and yaml file are stored')
@click.option('--f', default='definitions.yaml', help='The name of the yaml file in your directory')
def make_placeholders(d, f):
    def_file = open(os.path.join(d, f))
    definitions = yaml.safe_load(def_file)
    def_file.close()
    files = os.listdir(d)
    for file in files:
        if file != f:
            pt.set_image_tag(
                os.path.join(
                    d, file
                ),
                definitions[file]
            )
    print "Complete!"
    return

if __name__ == "__main__":
    make_placeholders()
#     make_placeholders(sys.argv[1], sys.argv[2])
