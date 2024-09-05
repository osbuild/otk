from .test_against_images_refs import _TestCase


def pytest_make_parametrize_id(config, val):  # pylint: disable=W0613
    # see https://hackebrot.github.io/pytest-tricks/param_id_func/ and
    # https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest.hookspec.pytest_make_parametrize_id
    if isinstance(val, _TestCase):
        return f"{val}"
    return None
