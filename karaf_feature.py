#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

"""
Ansible module to manage karaf features
(c) 2017, Matthieu Rémy <remy.matthieu@gmail.com>
"""

DOCUMENTATION = '''
---
module: karaf_feature
short_description: Install or uninstall Karaf features.
description:
    - Install or uninstall Karaf features.
options:
    name:
        description:
            - name of the feature to install or uninstall
        required: true
        default: null
    version:
        description:
            - version of the feature to install or uninstall
        required: false
        default: null
    state:
        description:
            - feature state
        required: false
        default: present
        choices: [ "present", "absent" ]
'''

EXAMPLES = '''
# Install karaf feature
- karaf_feature: state="present" name="camel-jms"

# Uninstall karaf feature
- karaf_feature: state="absent" name="camel-jms"

# Install karaf feature versioned
- karaf_feature: state="present" name="camel-jms" version="2.18.1"

# Uninstall multiple features
- name: "Uninstall features"
  karaf_feature: state="absent" name="{{ item.name }}" version="{{ item.version }}"
  with_items:
    - { name: "camel-jms", version: "2.18.1" }
    - { name: "camel-xml", version: "2.18.1" }

'''

PACKAGE_STATE_MAP = dict(
    present="install",
    absent="uninstall"
)

FEATURE_STATE_UNINSTALLED = 'Uninstalled'
CLIENT_KARAF_COMMAND = "{0} 'feature:{1}'"
CLIENT_KARAF_COMMAND_WITH_ARGS = "{0} 'feature:{1} {2}'"


def install_feature(client_bin, module, feature_name, feature_version):
    """Call karaf client command to install a feature

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param feature_name: name of feature to install
    :param feature_version: version of feature to install
    :return: command, ouput command message, error command message
    """
    full_qualified_name = feature_name
    if feature_version:
        full_qualified_name = full_qualified_name + "/" + feature_version
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP["present"], full_qualified_name)
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    # If feature is still uninstalled, fails.
    is_installed = is_feature_installed(client_bin, module, feature_name, feature_version)
    if not is_installed:
        module.fail_json(msg='Feature fails to install')

    return True, cmd, out, err


def uninstall_feature(client_bin, module, feature_name, feature_version):
    """Call karaf client command to uninstall a feature

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param feature_name: name of feature to install
    :param feature_version: version of feature to install
    :return: command, ouput command message, error command message
    """
    full_qualified_name = feature_name
    if feature_version:
        full_qualified_name = full_qualified_name + "/" + feature_version
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP["absent"], full_qualified_name)
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    is_installed = is_feature_installed(client_bin, module, feature_name, feature_version)
    if is_installed:
        module.fail_json(msg='Feature fails to uninstall')

    return True, cmd, out, err


def is_feature_installed(client_bin, module, feature_name, feature_version):
    """ Check if a feature with given version is installed.

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param feature_name: name of feature to install
    :param feature_version: version of feature to install. Optional.
    :return: True if feature is installed, False if not
    """

    cmd = CLIENT_KARAF_COMMAND.format(client_bin, 'list -i')
    rc, out, err = module.run_command(cmd)
    lines = out.split('\n')
    
    if not feature_version:
        feature_version = ''

    # Feature version in karaf use . instead of - when feature is deployed.
    # For instance, snapshot version will be 1.0.0.SNAPSHOT instead of 1.0.0-SNAPSHOT
    feature_version = feature_version.replace('-', '.')

    is_installed = False
    for line in lines:
        feature_data = line.split('\xe2\x94\x82')
        if len(feature_data) < 4:
            continue
        
        name = feature_data[0].strip()
        version = feature_data[1].strip()
        state = feature_data[3].strip()
        
        if name != feature_name:
            continue
        
        if state != FEATURE_STATE_UNINSTALLED:
            if feature_version:
                if version == feature_version:
                    is_installed = True
                    return is_installed
            else:
                is_installed = True
                return is_installed

    return is_installed


def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            version=dict(default=None),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        )
    )

    name = module.params["name"]
    version = module.params["version"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]

    is_installed = is_feature_installed(client_bin, module, name, version)
    changed = False
    cmd = ''
    out = ''
    err = ''
    if state == "present" and not is_installed:
        changed, cmd, out, err = install_feature(client_bin, module, name, version)
    elif state == "absent" and is_installed:
        changed, cmd, out, err = uninstall_feature(client_bin, module, name, version)

    module.exit_json(changed=changed, cmd=cmd, name=name, state=state, stdout=out, stderr=err)

if __name__ == '__main__':
    main()
