#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path

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

_KARAF_COLUMN_SEPARATOR = '\xe2\x94\x82'

def run_with_check(module, cmd):
    rc, out, err = module.run_command(cmd)
    
    bundle_id = None
    if  rc != 0 or \
        'Error executing command' in out or \
        'Command not found' in out:
        reason = out
        module.fail_json(msg=reason)
        raise Exception(out)

    return out

def get_existing_repos(module, client_bin):
    karaf_cmd = '%s "feature:repo-list"'
    out = run_with_check(module, karaf_cmd % (client_bin,))
    
    existing_repos = {}
    
    for line in out.split('\n'):
        split = line.split(_KARAF_COLUMN_SEPARATOR)

        if len(split) != 2:
            continue
        
        repo_name = split[0].strip()
        repo_url = split[1].strip()
        
        existing_repos[repo_url] = {
                'name': repo_name,
                'url': repo_url,
            }

    return existing_repos

def add_repo(client_bin, module, repo_url):
    """Call karaf client command to add a repo

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to add
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_PRESENT], repo_url)
    out = run_with_check(module, cmd)

    result = dict(
        changed=True,
        original_message='',
        message='',
        meta = {},
        out = out,
        cmd = cmd,
    )

    repos = get_existing_repos(module, client_bin)
    if repo_url not in repos:
        module.fail_json(msg='Repo ("%s") did not install' % repo_url)
        raise Exception(out)

    return result


def remove_repo(client_bin, module, repo_url):
    """Call karaf client command to remove a repo

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to remove
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_ABSENT], repo_url)
    out = run_with_check(module, cmd)

    result = dict(
        changed=True,
        original_message='',
        message='',
        meta = {},
        out = out,
        cmd = cmd,
    )

    repos = get_existing_repos(module, client_bin)
    if repo_url in repos:
        module.fail_json(msg='Repo ("%s") is still installed' % repo_url)
        raise Exception(out)

    return result


def refresh_repo(client_bin, module, repo_url):
    """Call karaf client command to refresh a repository

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param repo_url: url of repo to remove
    :return: command, ouput command message, error command message
    """
    cmd = CLIENT_KARAF_COMMAND_WITH_ARGS.format(client_bin, PACKAGE_STATE_MAP[STATE_REFRESH], repo_url)
    out = run_with_check(module, cmd)
    
    result = dict(
        changed=True,
        original_message='',
        message='',
        meta = {},
        out = out,
        cmd = cmd,
    )

    return result

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
    
    existing_repos = get_existing_repos(module, client_bin)

    result = dict(
        changed=False,
        original_message='',
        message='',
    )
    
    if state == STATE_PRESENT and url not in existing_repos:
        result = add_repo(client_bin, module, url)
    elif state == STATE_ABSENT and url in existing_repos:
        result = remove_repo(client_bin, module, url)
    elif state == STATE_REFRESH:
        if url not in existing_repos:
            module.fail_json(msg='The given repository ("%s") is not available and can therefore not be refreshed' % url)
        else:
            result = refresh_repo(client_bin, module, url)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
