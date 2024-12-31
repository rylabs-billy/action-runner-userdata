[![GitHub License](https://img.shields.io/github/license/rylabs-billy/action-runner-userdata?style=plastic)](https://github.com/rylabs-billy/action-runner-userdata/blob/main/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/rylabs-billy/action-runner-userdata/test.yml?branch=main&style=plastic&logo=github)](https://github.com/rylabs-billy/action-runner-userdata/actions/workflows/test.yml)
[![GitHub Marketplace](https://img.shields.io/badge/marketplace-action--runner--userdata-blue?style=plastic&logo=github)](https://github.com/marketplace/actions/self-hosted-runner-cloud-init-user-data)

# Self-hosted Runner Cloud-init User Data

Generates base64 encoded [cloud-config](https://cloudinit.readthedocs.io/en/latest/reference/examples.html#) user data for deploying a self-hosted GitHub Actions runner.

____
* [Usage](#usage)
* [Inputs](#inputs)
  * [scope](#name)
  * [name](#scope)
  * [runnergroup](#runnergroup)
  * [labels](#labels)
  * [work](#work)
  * [ephemeral](#ephemeral)
* [Outputs](#outputs)
  * [inputs](#inputs)
* [Contributing](#contributing)
* [Warnings](#warnings)

## Usage
Minimal example using defaults with the required conditional inputs (`repo` and `owner`).

```yaml
- name: Cloud-init user data for self-hosted runner
  id: cloud-config
  uses: rylabs-billy/action-runner-userdata@v1
  with:
    repo: postgres-cluster
    owner: rylabs-billy
  env:
    GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

Minimal example with an `organization` scope.
```yaml
- name: Cloud-init user data for self-hosted runner
  id: cloud-config
  uses: rylabs-billy/action-runner-userdata@v1
  with:
    scope: organization
    org: akamai-marketplace
  env:
    GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

Advanced example using all inputs to customize the runner [`./config.sh`](https://github.com/actions/runner/blob/main/src/Misc/layoutroot/config.sh) options, and passing the base64 encoded output to the next step.
```yaml
on:
  push:
    branches:
      - main

jobs:
  self-hosted-runner:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Generate cloud-init user data
        id: cloud-config
        uses: rylabs-billy/action-runner-userdata@v1
        with:
          scope: repository
          repo: postgres-cluster
          owner: rylabs-billy
          name: my_runner
          runnergroup: my_group
          labels: linode,cluster,dev,prod
          work: _work
          ephemeral: true
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}

     - name: Provision runner instance on Linode
       uses: linode/action-linode-cli@v1
       with:
        token: ${{ secrets.LINODE_TOKEN }}
       run: |
         linode-cli linodes create \
           --label linoderunner \
           --root_pass aComplex@Password \
           --region us-east \
           --type g6-standard-2 \
           --metadata.user_data "$USER_DATA"
       env:
         USER_DATA: ${{ toJson(steps.cloud-init.outputs.user-data) }}
```

## Inputs
This GitHub Action takes the following inputs:

### `scope` _(required)_
The scope of the runner. Can be for a single repository or for an organization. A `repository` scope (default) requires inputs for `owner` and `repo`.

Example: https://github.com/{owner}/{repo}

```yaml
scope: repository
owner: {owner}
repo: {repo}
```

An `organization` scope requires the `org` input.

Example: https://github.com/{org}

```yaml
scope: organization
org: {org}
```

### `name`

Name of the runner. If provided then `--replace` option is added to replace any existing runner with the same name in order to avoid naming conflicts. Otherwise the action defaults to generating a unique name by appending a timestamp to the repo or organization names.

(default `yyyy-mm-dd-hhmmss-<repo/org>`)


### `runnergroup`
Name of runner group to assign the runner in an organization.

(defaults to the default runner group)

### `labels`
Custom lables to apply in addition to the defaults.

(default `self-hosted`,`Linux`,`X64`)

### `work`
Relative work directory for the runner
      
(default `_work`)

### `ephemeral`
Configure the runner to take only one job, and then un-configure after the job finishes. This is recommend for public runners on public repositories to avoid security risks.
    
(default `true`)

## Outputs

### `user-data`
Base64 encoded cloud-init user data. Provide this output as the user-data parameter for a cloud provider's metadata service.

## Contributing

You want to improve **action-runner-userdata**! 😍 

Please open a [GitHub issue](../../issues/new/choose) to report bugs or suggest features, or follow the [fork and pull model](https://opensource.guide/how-to-contribute/#opening-a-pull-request) for open source contributions.

## Warnings

GitHub runners will display warnings for inputs not specified in `action.yml`.

This action takes three inputs that are conditionally required depending on the value of [scope](#scope). Those inputs are `repo`, `owner`, and `org`. Since they are conditionally dependent on the value of another input, statically defining them (each with its own `description`, `default` and `required` fields) would just add unnecessary bloat. For this reason they are **intentionally** excluded from `action.yaml`, which results in warnings such as the following:

```bash
Warning: Unexpected input(s) 'repo', 'owner', valid inputs are ['entryPoint', 'args', 'scope', 'name', 'runnergroup', 'labels', 'work', 'ephemeral']
```

These types of warnings can be ignored, as you will see them under normal usage. This action will error (not warn) if input requirements are not met. If it succeeds then everything should have worked properly.

For more information see:
- [Octokit Request Action- README](https://github.com/octokit/request-action/tree/v2.3.1?tab=readme-ov-file#warnings)
- [Octokit Request Action - Issue #26](https://github.com/octokit/request-action/issues/26)
- [substitute-string-action - Issue #1](https://github.com/bluwy/substitute-string-action/issues/1)
- [GitHub Community - Discussion #25387](https://github.com/orgs/community/discussions/25387)
- [GitHub Actions Runner - Issue #514](https://github.com/actions/runner/issues/514)
