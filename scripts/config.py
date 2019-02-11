# Preserve key ordering

import yaml
import yaml.representer


def represent_dict(dumper, data):
    return yaml.representer.SafeRepresenter.represent_dict(
        dumper, data.items())


yaml.add_representer(dict, represent_dict)
