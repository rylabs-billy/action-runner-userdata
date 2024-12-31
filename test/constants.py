# test/constants.py
from entrypoint import params

RUNNER_TOKEN = 'ALT2D6PL'
REPO = f"{params['owner']}/{params['repo']}"
ORG = f"{params['org']}"
API = "https://api.github.com"


# custom metaclass to make class attributes immutable
class Meta(type):
    def __setattr__(cls, name, value):
        for v in vars(cls):
            if name == v:
                raise AttributeError(f'Cannot modify attribute {v}')
            super().__setattr__(name, value)


class MockHTTP(metaclass=Meta):
    HEADERS = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer 12345',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    RESP = {
        'token': f'{RUNNER_TOKEN}',
        'expires_at': '2024-11-19T21:13:03.725-05:00'
    }
    ERR_RESP = {
        'message': 'Bad credentials',
        'documentation_url': 'https://docs.github.com/rest',
        'status': '401'
    }


class Urls(metaclass=Meta):
    REPO_URL = f"https://github.com/{params['owner']}/{params['repo']}"
    REPO_ENDPOINT = f"{API}/repos/{REPO}/actions/runners"
    ORG_ENDPOINT = f"{API}/orgs/{ORG}/actions/runners"


class Config(metaclass=Meta):
    TOKEN = f'{RUNNER_TOKEN}'
    OPTIONS = (
        '--name test-ea92885d '
        '--runnergroup test_group '
        '--labels test1,test2,test2 '
        '--work _work '
        '--ephemeral'
    )
