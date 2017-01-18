# Ansible karaf module

## Synopsys

This module wraps karaf console commands with ansible.
For now, You can manage karaf repositories and karaf features

## Karaf repositories management

### Options

| Parameter     | Required      | Default       | Choices           | Comments      |
| ------------- | ------------- | ------------- | ----------------- | ------------- |
| url           | yes           |               |                   | Maven url of the feature to install |
| state         | no            | present       |  present / absent | indicate the desired state of the resource |

### Examples

```yaml
# Install karaf repo
- karaf_repo: state=present url="mvn:org.apache.camel.karaf/apache-camel/2.18.1/xml/features"

# Uninstall karaf repo
- karaf_repo: state=absent url="mvn:org.apache.camel.karaf/apache-camel/2.18.1/xml/features"
```

## Karaf Features management

This module allow you to install / uninstall features on a karaf server.

When uninstalling a feature it launchs a ```feature:uninstall``` command in the karaf console, and then checks
with a ```feature:list``` the feature state, to be sure feature has been effectively uninstalled.

When installing a feature it launchs a ```feature:install``` command in the karaf console, and then checks
with a ```feature:list``` the feature state, to be sure feature has been effectively installed.

Be careful if you want to install multiple features, to first install the dependencies before the other features that depend on it.
Same thing if you want to uninstall multiple features, please first uninstall the features before the feature dependecies they depends on.
Otherwise the check for the state will fails.

### Options

| Parameter     | Required      | Default       | Choices       | Comments      |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| name           | yes          |               |               | Name of the feature to install |
| version        | no           |               |               | Version of the feature to install |
| state         | no            | present       |  present / absent | indicate the desired state of the resource |
 

### Examples

```yaml
# Install karaf feature
- karaf_feature: state=present name="camel-jms"

# Uninstall karaf feature
- karaf_feature: state=absent name="camel-jms"

# Install karaf feature versioned
- karaf_feature: state=present name="camel-jms" version="2.18.1"

# Uninstall multiple features
- name: "Uninstall features"
  karaf_feature: state="absent" name="{{ item.name }}" version="{{ item.version }}"
  with_items: 
    - { name: "camel-jms", version: "2.18.1" }
    - { name: "camel-xml", version: "2.18.1" }
```
