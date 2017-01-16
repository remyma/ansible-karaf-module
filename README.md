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
```
