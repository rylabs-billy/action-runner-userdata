# test/integration.py

import entrypoint
from entrypoint import params
from unittest.mock import patch
from .constants import (
    MockHTTP,
    Urls
)
from .helpers import (
    assert_request,
    assert_outputs
)


def _get_vars():
    # get runner name if provided
    if params['name']:
        runner_name = params['name']

    # set api endpoint url and runner name based on scope
    if params['scope'] == 'repository':
        url = Urls.REPO_ENDPOINT
        if not params['name']:
            runner_name = params['repo']
    else:
        url = Urls.ORG_ENDPOINT
        if not params['name']:
            runner_name = params['org']

    return url, runner_name


def test_integration(mock_post, capsys):
    url, runner_name = _get_vars()
    resp, endpoint = mock_post(url, MockHTTP.RESP)
    with patch('requests.post', return_value=resp) as post:
        entrypoint.main()

    captured = capsys.readouterr()
    assert_outputs(captured.out, runner_name)
    assert_request(post, endpoint, MockHTTP.HEADERS)
