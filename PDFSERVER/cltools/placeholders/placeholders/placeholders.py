import os
import sys
import click
import placeholder_tools as pt
import yaml
import warnings
warnings.filterwarnings("ignore")

@click.group()
def ts():
    password
@ts.command()
@click.argument('d')
@click.argument('f')
def tags(d, f):
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

@click.group()
def tg():
    pass
@tg.command()
@click.argument('f')
@click.argument('t')
def tag(f, t):
    pt.set_image_tag(
        f,
        t
        )
    print "Complete!"
    return

@click.group()
def gt():
    pass
@gt.command()
@click.argument('f')
def get_tag(f):
    message = pt.get_image_tag(
        f
        )
    print message
    return message
cli = click.CommandCollection(sources=[tg, ts, gt])
#

if __name__ == "__main__":
    cli()
#     make_placeholders(sys.argv[1], sys.argv[2])
