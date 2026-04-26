import site
from types import ModuleType
from unittest.mock import MagicMock

from django_completion.classify import classify_app


def _make_app(file_path: str) -> MagicMock:
    app = MagicMock()
    mod = ModuleType("fake_module")
    mod.__file__ = file_path
    app.module = mod
    return app


def test_pip_app():
    sp = site.getsitepackages()[0]
    app = _make_app(f"{sp}/some_package/__init__.py")
    assert classify_app(app) == "pip"


def test_local_app(settings, tmp_path):
    settings.BASE_DIR = str(tmp_path)
    local_file = tmp_path / "myapp" / "__init__.py"
    local_file.parent.mkdir()
    local_file.touch()
    app = _make_app(str(local_file))
    assert classify_app(app) == "local"


def test_unknown_falls_back_to_pip(tmp_path):
    # A path not under site-packages and not under BASE_DIR → pip
    app = _make_app(str(tmp_path / "somewhere" / "__init__.py"))
    assert classify_app(app) == "pip"


def test_no_file_attribute():
    app = MagicMock(spec=[])  # no .module attribute
    assert classify_app(app) == "pip"
