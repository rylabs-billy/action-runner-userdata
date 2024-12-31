# /usr/bin/env python3
# test/test.py

import os
import pytest
from requests.exceptions import HTTPError
from entrypoint import (
    runner_token,
    runner_scope,
    cloud_config,
    opts,
    params
)
from unittest.mock import patch
from .constants import (
    Config,
    MockHTTP,
    Urls
)
from .helpers import (
    assert_options,
    assert_request
)


def test_runner_token(mock_post):
    resp, endpoint = mock_post(Urls.REPO_ENDPOINT, MockHTTP.RESP)
    api_url = Urls.REPO_ENDPOINT
    with patch('requests.post', return_value=resp) as post:
        token = runner_token(api_url)

        assert token == 'ALT2D6PL'
        assert_request(post, endpoint, MockHTTP.HEADERS)


def test_runner_token_fail(mock_post, raise_for_status):
    api_url = Urls.REPO_ENDPOINT
    resp, endpoint = mock_post(
        Urls.REPO_ENDPOINT,
        MockHTTP.ERR_RESP,
        status_code=401
    )
    err = raise_for_status(resp, HTTPError, resp.json.return_value)

    with patch('requests.post', side_effect=err) as post:
        with pytest.raises(HTTPError) as p:
            try:
                runner_token(api_url)
            except SystemExit:
                raise err

        assert "Bad credentials" in str(p.value)
        assert_request(post, endpoint, MockHTTP.HEADERS)


def test_opts(mock_output_file, capsys):
    '''Test building commmand line options list'''
    try:
        open(os.environ['GITHUB_OUTPUT'], 'a').close()
    except KeyError:
        os.environ['GITHUB_OUTPUT'] = str(mock_output_file)

    # default (name generation)
    name = 'test'
    options_noname = opts(name)
    default_name = options_noname.split()[1]

    # optional inputs
    params['name'] = 'test-name'
    params['ephemeral'] = False
    options_name = opts(name)
    input_name = options_name.split()[1]

    # assert outputs
    captured = capsys.readouterr()
    assert f'runner-name={default_name}' in captured.out
    assert f'runner-name={input_name}' in captured.out
    assert_options([options_noname, options_name])


def test_runner_scope(scope_values):
    # repository (default)
    git_url, api_url, _name = runner_scope()
    for i in [git_url, api_url, _name]:
        assert i in scope_values['repository'].values()

    # organization
    params['scope'] = 'organization'
    git_url, api_url, _name = runner_scope()
    for i in [git_url, api_url, _name]:
        assert i in scope_values['organization'].values()


def test_cloud_config(capsys):
    token = Config.TOKEN
    options = Config.OPTIONS
    git_url = Urls.REPO_URL

    cloud_config(git_url, token, options)

    captured = capsys.readouterr()
    assert 'cloud-config data is valid' in captured.out
