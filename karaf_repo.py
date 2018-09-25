#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

"""
Ansible module to manage karaf repositories
(c) 2017, Matthieu Rémy <remy.matthieu@gmail.com>
"""

DOCUMENTATION = '''
---
module: karaf_repo
short_description: Manage karaf repositories.
description:
    - Manage karaf repositories in karaf console.
options:
    url:
        description:
            - path to the repo
        required: true
    state:
        description:
            - repo state
        required: false
        default: present
        choices: [ "present", "absent", "refresh" ]
    client_bin:
        description:
            - path to the 'client' program in karaf, can also point to the root of the karaf installation '/opt/karaf'
        required: false
        default: /opt/karaf/bin/client
'''

EXAMPLES = '''
# Install karaf repo
- karaf_repo: state="present" url="mvn:org.apache.camel.karaf/apache-camel/2.18.1/xml/features"

# Uninstall karaf repo
- karaf_repo: state="absent" url="mvn:org.apache.camel.karaf/apache-camel/2.18.1/xml/features"

# Refresh karaf repo
- karaf_repo: state="refresh" url="mvn:org.apache.camel.karaf/apache-camel/2.18.1/xml/features"
'''

STATE_PRESENT = "present"
STATE_ABSENT = "absent"
STATE_REFRESH = "refresh"

PACKAGE_STATE_MAP = dict(
    present="repo-add",
    absent="repo-remove",
    refresh="repo-refresh"

)

CLIENT_KARAF_COMMAND = "{0} 'feature:{1}'"
CLIENT_KARAF_COMMAND_WITH_ARGS = "{0} 'feature:{1} {2}'"


def add_repo(client_bin, module, repo_url):
    """Call karaf client command to add a repo

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to add
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_PRESENT], repo_url)
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    # TODO : check if repo is added.

    return True, cmd, out, err


def remove_repo(client_bin, module, repo_url):
    """Call karaf client command to remove a repo

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to remove
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_ABSENT], repo_url)
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    # TODO : check if repo is removed.

    return True, cmd, out, err


def refresh_repo(client_bin, module, repo_url):
    """Call karaf client command to refresh a repository

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to remove
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_REFRESH], repo_url)
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    return True, cmd, out, err


def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
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
        )
    )

    url = module.params["url"]
    state = module.params["state"]
    client_bin = module.params["client_bin"]

    client_bin = check_client_bin_path(client_bin)

    changed = False
    cmd = ''
    out = ''
    err = ''
    if state == STATE_PRESENT:
        changed, cmd, out, err = add_repo(client_bin, module, url)
    elif state == STATE_PRESENT:
        changed, cmd, out, err = remove_repo(client_bin, module, url)
    elif state == STATE_REFRESH:
        changed, cmd, out, err = refresh_repo(client_bin, module, url)

    module.exit_json(changed=changed, cmd=cmd, name=url, state=state, stdout=out, stderr=err)

if __name__ == '__main__':
    main()
