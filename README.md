# Ansible karaf module

## Synopsys

This module wraps karaf console commands with ansible.
For now, You can manage karaf repositories, features, bundles and config

## Karaf repositories management

### Options

| Parameter     | Required      | Default               | Choices           | Comments      |
| ------------- | ------------- | --------------------- | ----------------- | ------------- |
| url           | yes           |                       |                   | Maven url of the feature to install |
| state         | no            | present               |  present / absent | indicate the desired state of the resource |
| client_bin    | no            | /opt/karaf/bin/client |                   | path to the 'client' program in karaf |

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
| client_bin    | no            | /opt/karaf/bin/client |                   | path to the 'client' program in karaf |
 

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

## Karaf Bundles management

This module allow you to install / uninstall / refresh / ... bundles on a karaf server.

### Options

| Parameter     | Required      | Default       | Choices       | Comments      |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| url           | yes          |               |               | Url of the bundle to install |
| state         | no            | present       |  present / absent / start / stop / restart / refresh / update | indicate the desired state of the resource |
| client_bin    | no            | /opt/karaf/bin/client |                   | path to the 'client' program in karaf |
 

### Examples

```yaml
# Install karaf bundle
- karaf_bundle: state="present" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Uninstall karaf bundle
- karaf_bundle: state="absent" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Start karaf bundle
- karaf_bundle: state="start" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Stop karaf bundle
- karaf_bundle: state="stop" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"

# Refresh karaf bundle
- karaf_bundle: state="refresh" url="mvn:org.apache.camel/camel-example-osgi/2.15.2"
```

## Karaf Multi-Bundles management

This module allow you to install / uninstall / refresh / ... multiple bundles on a karaf server.

### Options

| Parameter     | Required      | Default       | Choices       | Comments      |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| urls          | yes          |               |               | Urls of the bundles to install. This must be a list |
| state         | no            | present       |  present / absent / start / stop / restart / refresh / update | indicate the desired state of the resource |
| client_bin    | no            | /opt/karaf/bin/client |                   | path to the 'client' program in karaf |
 

### Examples

```yaml
# Install karaf bundles
- karaf_bundles: 
    state: present 
    urls:
      - mvn:org.apache.camel/camel-example-osgi/2.15.2
      - mvn:com.google.code.gson/gson/2.8.5

# Uninstall karaf bundles
- karaf_bundles: 
    state: absent 
    urls:
      - mvn:org.apache.camel/camel-example-osgi/2.15.2
      - mvn:com.google.code.gson/gson/2.8.5

# Start karaf bundles
- karaf_bundles: 
    state: start 
    urls:
      - mvn:org.apache.camel/camel-example-osgi/2.15.2
      - mvn:com.google.code.gson/gson/2.8.5

# Stop karaf bundles
- karaf_bundles: 
    state: stop
    urls:
      - mvn:org.apache.camel/camel-example-osgi/2.15.2
      - mvn:com.google.code.gson/gson/2.8.5

# Refresh karaf bundles
- karaf_bundles: 
    state: refresh
    urls:
      - mvn:org.apache.camel/camel-example-osgi/2.15.2
      - mvn:com.google.code.gson/gson/2.8.5
```

## Karaf Configuration management

This module allow you to edit configurations on a karaf server.

### Options

| Parameter     | Required      | Default       | Choices       | Comments      |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| name          | yes           |               |                      | Name of the service PID |
| properties    | yes           |               |                      | dictionary with key and values to set, in case of absent, then only the key is necessary |
| state         | no            | present       |  present / absent    | indicate the desired state of the property |
| client_bin    | no            | /opt/karaf/bin/client |              | path to the 'client' program in karaf |
 

### Examples

```yaml
# Set config properties on PID org.apache.karaf.kar
- karaf_config:
    name: org.apache.karaf.kar
    state: present
    properties:
      noAutoStartBundles: false
      noAutoRefreshBundles: false

# In case of removing a property, only the key in 'properties' is necessary
- karaf_config:
    name: org.apache.karaf.kar
    state: absent
    properties:
      noAutoRefreshBundles:
```
