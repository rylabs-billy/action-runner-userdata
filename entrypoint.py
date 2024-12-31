#!/usr/bin/env python3
# entrypoint.py

import os
import uuid
import requests
import base64
import subprocess

PACKAGE = 'actions-runner-linux-x64-2.300.2.tar.gz'
PACKAGE_URL = 'https://github.com/actions/runner/releases/download/v2.300.2/'
SHA256 = 'ed5bf2799c1ef7b2dd607df66e6b676dff8c44fb359c6fedc9ebf7db53339f0c'
GH_TOKEN = os.environ.get('GH_TOKEN')

# inputs
params = {
    'scope': os.environ.get('SCOPE'),
    'repo': os.environ.get('REPO'),
    'owner': os.environ.get('OWNER'),
    'org': os.environ.get('ORG'),
    'name': os.environ.get('NAME'),
    'runnergroup': os.environ.get('RUNNERGROUP'),
    'labels': os.environ.get('LABELS'),
    'work': os.environ.get('WORK'),
    'ephemeral': str(os.environ.get('EPHEMERAL'))
}


# error messages
def _err(error):
    if error == 'repo_err':
        print(
            "::error title=missing input"
            "::repository scope requires 'owner' and 'repo' inputs"
        )
    elif error == 'org_err':
        print(
            "::error title=missing input"
            "::organization scope requires 'org' input"
        )
    elif error == 'input_err':
        print(
            "::error title=invalid input"
            "scope requires input values of 'repository' or 'organization'"
        )
    elif error == 'config_err':
        print(
            "::error title=invalid cloud-config"
            "::yaml formatting error."
        )
    elif error == 'github_err':
        print(
            "::error title=api error"
            "::github api returned an error response."
        )
    exit(1)


def _chk_config(config):
    # check that our schema is valid after decoding
    with open('test.yml', 'w') as f:
        d = base64.b64decode(config).decode()
        f.write(d)

    cmd = ['cloud-init', 'schema', '-c', 'test.yml', '--annotate']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print('cloud-config data is valid')
    else:
        _err('config_error')


def runner_scope():
    '''Validate inputs to build params'''
    # scope dependent inputs
    if params['scope'].lower() == 'repository':
        if params['owner'] and params['repo']:
            path = f'{params["owner"]}/{params["repo"]}'
            api_group = 'repos'
            _name = params['repo']
        else:
            _err('repo_err')
    elif params['scope'].lower() == 'organization':
        if params['org']:
            path = params['org']
            _name = params['org']
            api_group = 'orgs'
        else:
            _err('org_err')
    else:
        _err('input_err')

    git_url = f'{os.environ["GITHUB_SERVER_URL"]}/{path}'
    api_url = f'https://api.github.com/{api_group}/{path}/actions/runners'

    return git_url, api_url, _name


def opts(_name):
    '''Runner config options'''
    opts = []
    inputs = ['runnergroup', 'labels', 'work']

    # build list of optional key/value inputs
    for i in inputs:
        if params[i]:
            opts.append(f'--{i} {params[i]}')

    # append ephemeral if set to 'true'
    if params['ephemeral'] == 'true':
        opts.append('--ephemeral')

    # add --replace if name param is provided to prevent conflicts
    # auto generate from repo/org when not specified
    if params['name']:
        name = params['name']
        opts.append('--replace')
    else:
        _ = str(uuid.uuid4()).split('-')[0]
        name = f'{_name}-{_}'
    
    # insert name as first element in opts list
    opts.insert(0, f'--name {name}')

    # add runner name to GITHUB_OUTPUT
    with open(os.environ['GITHUB_OUTPUT'], 'a+') as f:
        print(f'runner-name={name}', file=f)
        f.seek(0)
        last_line = f.readlines()[-1]
        print(last_line)

    options = ' '.join(opts)
    print(f'options: {options}')
    return options


def runner_token(api_url):
    '''Create self-hosted runner token'''
    url = f'{api_url}/registration-token'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {GH_TOKEN}',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    try:
        resp = requests.post(url, headers=headers)
        resp.raise_for_status()
        token = resp.json()['token']
        print(f'::add-mask::{token}')
    except requests.exceptions.RequestException as errex:
        print(errex)
        _err('github_err')

    return token


def cloud_config(git_url, token, options):
    '''Generate cloud config data'''
    config = (f'''
    #cloud-config
    package_update: true
    package_upgrade: true
    runcmd:
      - sysctl -w net.ipv6.conf.all.disable_ipv6=1
      - sysctl -w net.ipv6.conf.default.disable_ipv6=1
      - sysctl -w net.ipv6.conf.lo.disable_ipv6=1
      - mkdir /root/actions-runner
      - cd /root/actions-runner
      - curl -o {PACKAGE} -L {PACKAGE_URL}/{PACKAGE}
      - echo '{SHA256}  {PACKAGE}' | sha256sum -c
      - tar xzf ./{PACKAGE}
      - ./bin/installdependencies.sh
      - export RUNNER_ALLOW_RUNASROOT='1'
      - echo "HOME=/root" > .env
      - ./config.sh --unattended --url {git_url} --token {token} {options}
      - ./run.sh
    ''')

    # base64 encode, strigify, and validate user data
    data = base64.b64encode(config.encode('utf-8'))
    user_data = data.decode('utf-8')
    print(f'::add-mask::{user_data}')
    _chk_config(user_data)

    with open(os.environ['GITHUB_OUTPUT'], 'a+') as f:
        print(f'user-data={user_data}', file=f)

def main():
    print(params)
    git_url, api_url, _name = runner_scope()
    options = opts(_name)
    token = runner_token(api_url)
    cloud_config(git_url, token, options)


# main
if __name__ == '__main__':
    main()
