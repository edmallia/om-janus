## Introduction

### About the name - Janus

## Python Versions

Developed and tested using,

- Python v3.11.5
- Pip v23.3.2

## Installation

```bash
git clone https://github.com/edmallia/om-janus.git
cd om-janus
pip install -r requirements.txt
```

## Running Janus
### Check version

```bash
python -m janus version
```

![version](./docs/img/version.png)

### Show help

```bash
python -m janus --help
```

![help](./docs/img/help.png)

### Show help for Alert Configs subcommand

```bash
python -m janus alert-configs --help
```

![alertconfighelp](./docs/img/alertconfighelp.png)

### Export Alert Configs

```bash
python -m janus alert-configs export
```
Following on screen instructions.

![exportwithinput](./docs/img/exportwithinput.png)


### Export Alert Configs using a Configuration file

```bash
python -m janus alert-configs export --config config.yaml
```

![exportwithconfig](./docs/img/exportwithconfig.png)

Following on screen instructions.

### Import Alert Configs

``` bash
python -m janus alert-configs import
```

![importwithinput](./docs/img/importwithinput.png)

Following on screen instructions.

### Import Alert Configs using a Configuration file

``` bash
python -m janus alert-configs import --config config.yaml
```

Following on screen instructions.

![importwithconfig](./docs/img/importwithconfig.png)

### Sample Configuration file

```yaml
sourceUrl: http://localhost:8080
sourceUsername: xxxxxxxx
sourceApiKey: 00000000-0000-0000-0000-000000000000
outputFile: alertConfigs.json

destinationUrl: http://localhost:8080
destinationUsername: xxxxxxxx
destinationApiKey: 00000000-0000-0000-0000-000000000000
detectAndSkipDuplicates: true
inputFile: alertConfigs.json
```
