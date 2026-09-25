import os

from lemming.utils import get_safe_env


def test_get_safe_env_strips_secrets():
    os.environ['OPENAI_API_KEY'] = 'secret'
    os.environ['MY_TOKEN'] = 'secret_token'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'aws_secret'
    os.environ['NORMAL_VAR'] = 'normal'

    env = get_safe_env()
    assert 'OPENAI_API_KEY' not in env
    assert 'MY_TOKEN' not in env
    assert 'AWS_SECRET_ACCESS_KEY' not in env
    assert env['NORMAL_VAR'] == 'normal'

def test_get_safe_env_allows_explicit_overrides():
    os.environ['OPENAI_API_KEY'] = 'secret'

    env = get_safe_env({'SOME_VAR': 'val', 'MY_TOKEN': 'explicit'})
    assert 'OPENAI_API_KEY' not in env
    assert env['SOME_VAR'] == 'val'
    assert env['MY_TOKEN'] == 'explicit'
