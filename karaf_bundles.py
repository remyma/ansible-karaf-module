#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: karaf_bundles
short_description: Karaf console commands to Manage multiple OSGi bundles.
description:
    - Karaf console commands to Manage multiple OSGi bundles.
options:
    urls:
        description:
            - Urls of the bundles to install or uninstall
        required: true
        type: list
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
# Install karaf bundles
- karaf_bundles: 
    state: present 
    urls: 
      - mvn:com.google.code.gson/gson/2.8.5
      - mvn:com.google.code.gson/gson/2.8.4
      - mvn:com.google.code.gson/gson/2.8.3
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

def launch_bundles_action(client_bin, module, bundles, state):
    """Call karaf client command to execute a bundle action on a bundle id

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param bundles: list of bundle to execute action on 
    :param action: bundle action to perform
    :return: command, ouput command message, error command message
    """
    karaf_action = PACKAGE_STATE_MAP[state]

    result = dict(
        changed=False,
        original_message='',
        message='',
        meta = {}
    )
    
    affected_bundles = bundles

    if karaf_action == 'start':
        # Check if we need to start any bundle
        stoped_bundles = [b for b in bundles if b['state'] != 'Active']
        if len(stoped_bundles) < 1:
            result['meta']['msg'] = 'All bundles already started'
            return result
        
        affected_bundles = stoped_bundles
        
    elif karaf_action == 'stop':
        # Check if there are any bundles that we need to stop
        active_bundles = [b for b in bundles if b['state'] == 'Active']
        if len(active_bundles) < 1:
            result['meta']['msg'] = 'No running bundles found'
            return result
            
        affected_bundles = active_bundles
        
    result['changed'] = True
    if module.check_mode:
        return result
    
    karaf_cmd_base = 'bundle:%s %s'
    bundles_dict_key= 'url' if karaf_action == 'install' else 'id'
    
    cmds = [karaf_cmd_base % (karaf_action, b[bundles_dict_key]) for b in affected_bundles]
    
    out = run_with_check(module, '%s "%s"' % (client_bin, ' && '.join(cmds)))
    
    return result

def is_bundles_installed(client_bin, module, urls):
    tmp = frozenset(urls)
    
    karaf_cmd = '%s "bundle:list -t 0 -u"' % (client_bin)
    out = run_with_check(module, karaf_cmd)
    
    existing_bundles = {}
    
    for line in out.split('\n'):
        columns = [e.strip() for e in line.split(_KARAF_COLUMN_SEPARATOR)]
        
        if len(columns) < 3:
            continue

        if columns[4] not in tmp:
            continue
        
        existing_bundles[columns[4]] = {
            'id':           int(columns[0]),
            'state':        columns[1],
            'start_level':  int(columns[2]),
            'version':      columns[3],
            'url':          columns[4]
            }

    return existing_bundles

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
            urls=dict(required=True, type='list'),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        ),
        supports_check_mode=True
    )
    
    result = dict(
        changed=False,
        original_message='',
        message='',
    )

    urls = module.params["urls"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]

    client_bin = check_client_bin_path(client_bin)

    existing = is_bundles_installed(client_bin, module, urls)
    
    if state == 'present':
        needs_install = [{'url': bnd_url} for bnd_url in urls if bnd_url not in existing]
        if not needs_install:
            module.exit_json(**result)
            return
        
        result = launch_bundles_action(client_bin, module, needs_install, state)
        
    else:
        not_installed = [bnd_url for bnd_url in urls if bnd_url not in existing]
        if not_installed:
            module.fail_json(msg="The following bundles are not installed: %s"  % (', '.join(not_installed)))
            return

        result = launch_bundles_action(client_bin, module, existing.values(), state)

    
#     module.fail_json(msg=str(existing))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
