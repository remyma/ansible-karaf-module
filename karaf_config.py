#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path

DOCUMENTATION = '''
---
module: karaf_config

short_description: A module for manipulating the configuration in a running karaf instance

version_added: "2.5"

description:
    - Set or delete one or more properties in a running karaf instance

options:
    name:
        description:
            - name of the service pid
        required: true
    properties:
        description:
            - a dictionary with property name (key) and its value
        required: true
        type: dict
    state:
        description:
            - property state
        required: false
        default: present
        choices: [ "present", "absent" ]
    client_bin:
        description:
            - path to the 'client' program in karaf, can also point to the root of the karaf installation '/opt/karaf'
        required: false
        default: /opt/karaf/bin/client
'''

EXAMPLES = '''
# Set a property
- name: Test with a message
  karaf_config:
    name: org.apache.karaf.kar
    state: present
    properties:
      noAutoStartBundles: false
      
# Remove property
- name: Test2 - Delete config
  karaf_config:
    name: org.apache.karaf.kar
    state: absent
    properties:
      key1:                
'''

PACKAGE_STATE_MAP = dict(
    present="property-set",
    absent="property-delete"
)

_BOOL_TYPES = frozenset(['true', 'false', 'yes', 'no', 'y', 'n'])

def check_bool(value):
    if not value.lower() in _BOOL_TYPES:
        raise ValueError()
    
    v = value.lower()
    return  v == 'true' or \
            v == 'yes' or \
            v == 'y'
    
def convert(val):
    constructors = [int, float, check_bool, str]
    for c in constructors:
        try:
            return c(val);
        except ValueError:
            pass

def run_with_check(module, cmd):
    rc, out, err = module.run_command(cmd)
    
    if  rc != 0 or \
        'Error executing command' in out or \
        'Command not found' in out:
        reason = out
        module.fail_json(msg=reason)
        raise Exception(out)

    return out

def existing_properties(module, client_bin, name, new_properties):
    cmd_base = 'config:property-get --raw --pid %s %s'
    karaf_cmd = ' && '.join([cmd_base % (name, prop) for prop in new_properties.keys()])

    out = run_with_check(module, '%s "%s"' % (client_bin, karaf_cmd))    
    lines = out.split('\n')
    result = {}
    
    for line in lines:
        if '=' not in line:
            continue
        
        i = line.find('=')
        prop_name = line[:i].strip()
        value = convert(line[i+1:].strip())
            
        result[prop_name] = value
    
    return result

def config_property_set(client_bin, module, name, new_properties):
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    existing_props = existing_properties(module, client_bin, name, new_properties)
    need_change = [k for k,v in new_properties.items() if k not in existing_props or existing_props[k] != v]
        
    if not need_change:
        return result
    
    result['changed'] = True
    if module.check_mode:
        return result

    cmd_base = 'config:property-set %s %s'
    
    cmds = []
    cmds.append('config:edit %s' % name)  
    cmds.extend([cmd_base % (k, v) for k,v in new_properties.items() if k in need_change])
    cmds.append("config:update")
    cmd = ' && '.join(cmds)
    out = run_with_check(module, '%s "%s"' % (client_bin, cmd))
    
    return result

def config_property_delete(client_bin, module, name, properties):
    result = dict(
        changed=False,
        original_message='',
        message='',
    )
    
    existing_props = existing_properties(module, client_bin, name, properties)
    
    need_delete = [k for k in properties.keys() if k in existing_props]
    
    if not need_delete:
        return result
    
    result['changed'] = True
    if module.check_mode:
        return result
    
    cmd_base = 'config:property-delete --pid "%s" %s'
    cmd = ' && '.join([ cmd_base % (name, k) for k in properties.keys() if k in need_delete])
    run_with_check(module, '%s "%s"' % (client_bin, cmd))
    return result

def check_client_bin_path(client_bin):
    if os.path.isfile(client_bin):
        return client_bin
    
    if os.path.isdir(client_bin):
        test = os.path.join(client_bin, 'bin/client')
        if os.path.isfile(test):
            return test
    else:
        raise Exception('client_bin parameter not supported: %s' % client_bin)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            properties=dict(required=True, type="dict"),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        ),
        supports_check_mode=True
    )

    name = module.params["name"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]
    properties = module.params["properties"]
    
    client_bin = check_client_bin_path(client_bin)
    
    if state == "present":
        result = config_property_set(client_bin, module, name, properties)
    elif state == "absent":
        result = config_property_delete(client_bin, module, name, properties)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
