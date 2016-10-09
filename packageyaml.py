import yaml

with open('package.txt') as f:
    content = f.readlines()

obj = {'template_logo': '', 'template_scripts': [], 'template_rules': []}
rules = []
for i, e in enumerate(content):
    pieces = e.split(';')
    name = pieces[1]
    package_key = pieces[len(pieces)-2]
    rules.append({
        'rule': {
            'package_key': package_key,
            'package_name': name,
            'included_templates': []
        }
    })
obj['template_rules'] = rules

with open('package.yaml', 'w') as outfile:
    yaml.dump(obj, outfile, default_flow_style=False)
    # print name
    # print package_key
