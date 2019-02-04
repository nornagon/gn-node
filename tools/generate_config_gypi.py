import re
import os
import pprint
import subprocess
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(root_dir, "node", "tools"))
import getmoduleversion

GN_RE = re.compile(r'(\w+)\s+=\s+(.*?)$', re.MULTILINE)

def bool_to_number(v):
  return 1 if v == "true" else 0

def load_template(template_file):
  with open(template_file, "r") as f:
    return f.read()

def main(gn_out_dir, template_file, output_file, depfile):
  # Get GN config and parse into a dictionary.
  gnconfig = subprocess.check_output(
                 ["gn", "args", "--list", "--short", "-C", gn_out_dir])
  config = dict(re.findall(GN_RE, gnconfig))

  config["node_module_version"] = getmoduleversion.get_version()

  # Fill in template.
  template = {
    "target_defaults": {
      "default_configuration": "Debug" if config['is_debug'] else "Release"
    },

    "variables": {
      # necessary for running js tests
      "node_module_version": config['node_module_version'],
      "node_report": config['node_report'],
      "node_shared": bool_to_number(config['is_component_build']),
      # v8_enable_inspector is a misnomer, since this is actually a node config
      "v8_enable_inspector": bool_to_number(config['node_enable_inspector']),
      "v8_enable_i18n_support": bool_to_number(config['v8_enable_i18n_support']),

      # introduced for building addons
      "node_use_openssl": config['node_use_openssl'],
      "build_v8_with_gn": "false",
      "enable_lto": "false",
      "openssl_fips": "",
    }
  }
  if config['node_use_code_cache'] == 'true':
    template['variables']['node_code_cache_path'] = 'node_code_cache.cc'
  rendered_template = pprint.pformat(template)

  # Write output.
  with open(output_file, "w") as f:
    f.write(rendered_template)

  # Write depfile. Force regenerating config.gypi when GN configs change.
  with open(depfile, "w") as f:
    dot_gn = os.path.abspath(os.path.join(root_dir, ".gn"))
    args_gn = os.path.abspath(os.path.join(gn_out_dir, "args.gn"))
    f.write("%s: %s %s" %(output_file, dot_gn, args_gn))

if __name__ == '__main__':
  main(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
