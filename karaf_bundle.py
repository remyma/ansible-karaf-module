#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path

"""
Ansible module to manage karaf bundles
(c) 2017, Matthieu Rémy <remy.matthieu@gmail.com>
"""

DOCUMENTATION = '''
---
module: karaf_bundle
short_description: Karaf console commands to Manage Osgi bundles.
description:
    - Karaf console commands to Manage Osgi bundles.
options:
    url:
        description:
            - Url of the bundles to install or uninstall
        required: true if state is "present"
        default: null
    state:
        description:
            - bundle state
        required: false
        default: present
        choices: [ "present", "absent", "start", "stop", "restart", "refresh", "update" ]
    client_bin:
        description:
            - path to the 'client' program in karaf, can also point to the root of the karaf installation '/opt/karaf'
        required: false
        default: /opt/karaf/bin/client
'''

EXAMPLES = '''
# Install karaf bundle
- karaf_bundle: state="present" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Uninstall karaf bundle
- karaf_bundle: state="absent" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Refresh karaf bundle
- karaf_bundle: state="refresh" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

'''

PACKAGE_STATE_MAP = dict(
    present="install",
    absent="uninstall",
    start="start",
    stop="stop",
    restart="restart",
    refresh="refresh",
    update="update"
)

CLIENT_KARAF_COMMAND = "bundle:{0}"
CLIENT_KARAF_COMMAND_WITH_ARGS = "bundle:{0} {1}"

_KARAF_COLUMN_SEPARATOR = '\xe2\x94\x82'

def run_with_check(module, cmd, arg):
    rc, out, err = module.run_command('%s -b' % (cmd,), data=arg)
    
    if  rc != 0 or \
        'Error executing command' in out or \
        'Command not found' in out or\
        len(err) > 0:
        reason = out
        module.fail_json(msg=reason, cmd=cmd, cmd_err=err, cmd_return=rc)
        raise Exception(out)

    return out

def launch_bundle_action(client_bin, module, url, bundle_id, action):
    """Call karaf client command to execute a bundle action on a bundle id

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param url: url of bundle to install
    :param bundle_id: id of bundle to execute action
    :param action: bundle action to perform
    :return: command, ouput command message, error command message
    """
    result = dict(
        changed=True,
        original_message='',
        name = bundle_id,
        message='',
    )
    
    if module.check_mode:
        return result
    
    bnd_ref = url if action == 'install' else bundle_id

    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(action, bnd_ref)
    out = run_with_check(module, client_bin, cmd)
    
    return result

def is_bundles_installed(client_bin, module, bundle_url):
    karaf_cmd = 'bundle:list -t 0 -u'
    out = run_with_check(module, client_bin, karaf_cmd)
    
    existing_bundle = None
    
    for line in out.split('\n'):
        if line[-len(bundle_url):] != bundle_url:
            continue
        
        columns = [e.strip() for e in line.split(_KARAF_COLUMN_SEPARATOR)]

        existing_bundle = {
            'id':           int(columns[0]),
            'state':        columns[1],
            'start_level':  int(columns[2]),
            'version':      columns[3],
            'url':          columns[4]
            }
    
    return existing_bundle

def parse_error(string):
    return string

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
            url=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        ),
        supports_check_mode=True
    )

    url = module.params["url"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]
    
    client_bin = check_client_bin_path(client_bin)

    existing_bundle = is_bundles_installed(client_bin, module, url)
    
    # Bundle is installed
    if existing_bundle is not None:
        if  state == 'present' and \
            existing_bundle['url'] == url:
            return module.exit_json(changed=False, name=existing_bundle['id'], msg = 'Bundle already installed')

        if state == 'start' and existing_bundle['state'] == 'Active':
            return module.exit_json(changed = False, name=existing_bundle['id'], msg = 'Bundle already started')

        if state == 'stop' and existing_bundle['state'] != 'Active':
            return module.exit_json(changed = False, name=existing_bundle['id'], msg = 'Bundle already stopped')
    
    # if no bundle installed with given URL
    else:
        if state != 'present':
            return module.fail_json(msg = "Can not execute action on a non-existing bundle, Could not find a bundle installed with URL: %s" % (url,))

    result = launch_bundle_action(
            client_bin,
            module, 
            url, 
            existing_bundle['id'] if existing_bundle is not None else None, 
            PACKAGE_STATE_MAP[state]
            )

    module.exit_json(**result)

if __name__ == '__main__':
    main()
