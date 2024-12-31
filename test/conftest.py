import os
import re
import pytest
from typing import Union
from entrypoint import params
from unittest.mock import Mock


@pytest.fixture
def mock_output_file(tmp_path):
    file_path = tmp_path / 'tmpfile'
    open('tmpfile', 'a').close()
    yield file_path

    if os.path.exists('tmpfile'):
        os.remove('tmpfile')


@pytest.fixture(scope='session')
def mock_response():
    def _build(status_code: int, data: dict) -> any:
        # setup mocks
        resp = Mock()
        resp.status_code = status_code
        resp.json.return_value = data

        return resp

    yield _build


@pytest.fixture(scope='function')
def raise_for_status():
    def _error(
        mocked_object: object,
        error: object,
        exeinfo: Union[str, dict]
    ) -> any:
        e = mocked_object
        # err = e.raise_for_status.side_effect = error(exeinfo)
        err = e.raise_for_status.side_effect = error(exeinfo)

        return err

    yield _error


@pytest.fixture(scope='function')
def scope_values():
    # shorten variable names
    url = os.environ.get('GITHUB_SERVER_URL')
    api = re.sub('github', 'api.github', url, 1)
    owner = params['owner']
    repo = params['repo']
    org = params['org']

    scope_data = {
        'repository': {
            'git_url': f'{url}/{owner}/{repo}',
            'api_url': f'{api}/repos/{owner}/{repo}/actions/runners',
            '_name': f'{repo}'
        },
        'organization': {
            'git_url': f'{url}/{org}',
            'api_url': f'{api}/orgs/{org}/actions/runners',
            '_name':  f'{org}'
        }
    }

    yield scope_data


@pytest.fixture(scope='function')
def github_output(mock_output_file):
    try:
        with open(os.environ['GITHUB_OUTPUT'], 'a+'):  # as f:
            pass
    except KeyError:
        os.environ['GITHUB_OUTPUT'] = str(mock_output_file)


@pytest.fixture(scope='function')
def mock_post(mock_response, github_output):
    def _post(endpoint: str, response: dict, status_code: int = 201) -> any:
        resp = mock_response(status_code=status_code, data=response)
        endpoint = f'{endpoint}/registration-token'

        return resp, endpoint

    yield _post
