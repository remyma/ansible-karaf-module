#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

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

CLIENT_KARAF_COMMAND = "{0} 'bundle:{1}'"
CLIENT_KARAF_COMMAND_WITH_ARGS = "{0} 'bundle:{1} {2}'"

_KARAF_COLUMN_SEPARATOR = '\xe2\x94\x82'

def run_with_check(module, cmd):
    rc, out, err = module.run_command(cmd)
    
    bundle_id = None
    if  rc != 0 or \
        'Error executing command' in out or \
        'Command not found' in out:
        reason = parse_error(out)
        module.fail_json(msg=reason)
        raise Exception(out)

    return out

def install_bundle(client_bin, module, bundle_url):
    """Call karaf client command to install a bundle

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param bundle_url: maven url of bundle to install
    :return: changed, command, bundle_id, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP["present"], bundle_url)
    run_with_check(module, cmd)
    
    install_result = out.split(':')
    bundle_id = install_result[1].strip()

    # Parse out to get Bundle id.
    return True, cmd, bundle_id, out, err


def launch_bundle_action(client_bin, module, bundle_id, action):
    """Call karaf client command to execute a bundle action on a bundle id

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param bundle_id: id of bundle to install
    :param action: bundle action to perform
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, action, bundle_id)
    out = run_with_check(module, cmd)

    return True, cmd, out, ''

def is_bundles_installed(client_bin, module, bundle_url):
    karaf_cmd = '%s "bundle:list -t 0 -u"' % (client_bin)
    out = run_with_check(module, karaf_cmd)
    
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

def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        )
    )

    url = module.params["url"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]
    
    existing_bundle = is_bundles_installed(client_bin, module, url)
    
    if  state == 'present' and \
        existing_bundle is not None and \
        existing_bundle['url'] == url:
        return module.exit_json(changed=False, cmd='', name=existing_bundle['id'], state=state, stdout='', stderr='')

    # Get Bundle id by executing an install. If bundle is already installed, it will return bundle id.
    changed, cmd, bundle_id, out, err = install_bundle(client_bin, module, url)

    if bundle_id:
        changed, cmd, out, err = launch_bundle_action(client_bin, module, bundle_id, state)

    module.exit_json(changed=changed, cmd=cmd, name=bundle_id, state=state, stdout=out, stderr=err)

if __name__ == '__main__':
    main()
