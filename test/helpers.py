# test/helpers.py
from entrypoint import params


# helper functions
def assert_options(options: list):
    '''Helper for asserting command line options'''
    for i in options:
        n = i.split()[1]
        e = i.split()[-1]
        base = (
            f'--name {n} '
            f'--runnergroup {params["runnergroup"]} '
            f'--labels {params["labels"]} '
            f'--work {params["work"]} '
        )
        if e == '--ephemeral' or e == '--replace':
            final_str = base + e
            assert i == final_str
        else:
            raise AssertionError(
                'Options (string) must end with: --(ephemeral|replace)\n\n'
                'Expected one of:\n'
                f'\t{base}--ephemeral\n'
                f'\t{base}--replace\n'
                f'\t{base}--ephemeral --replace\n'
                f'Actual: {i}'
            )


def assert_request(mocked_method: any, endpoint: str, headers: dict):
    mocked_method.assert_called_once()
    mocked_method.assert_called_with(endpoint, headers=headers)


def assert_outputs(capture_file: str, runner_name: str):
    chk_str = [
        f'runner-name={runner_name}',
        '::add-mask::ALT2D6PL',
        'cloud-config data is valid'
    ]
    for output in chk_str:
        assert output in capture_file
