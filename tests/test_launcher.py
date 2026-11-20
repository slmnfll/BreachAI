import pytest
import runpy
from pathlib import Path
from types import SimpleNamespace


def test_direct_launch_uses_current_python_and_project_directory(monkeypatch, tmp_path):
    import sys
    root = Path(__file__).resolve().parents[1]
    calls = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('subprocess.run',
                        lambda command, cwd, **kwargs: calls.append((command, cwd, kwargs)) or SimpleNamespace(
                            returncode=0))
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(root / 'app.py'), run_name='__main__')
    assert result.value.code == 0
    command, cwd, options = calls[0]
    assert options["input"] == "\n"
    assert cwd == root
    assert command[:4] == [sys.executable, '-m', 'streamlit', 'run']
    assert command[4] == str(root / 'app.py')
    assert '--server.address=127.0.0.1' in command
