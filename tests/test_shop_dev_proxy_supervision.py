import plistlib
from pathlib import Path
import pytest
from ops.macos.shopping.dev_order_https_proxy import launch_agent

def test_supervised_proxy_pins_release_and_survives_terminal_exit(tmp_path):
    release=tmp_path/'release';script=release/'ops/macos/shopping/dev_order_https_proxy.py'
    script.parent.mkdir(parents=True);script.write_text('# fixture')
    python=tmp_path/'python';python.write_text('# fixture')
    private=tmp_path/'private';private.mkdir()
    value=plistlib.loads(launch_agent(release,python,private))
    assert value['RunAtLoad'] and value['KeepAlive']
    assert value['ProgramArguments']==[str(python),str(script)]
    assert value['WorkingDirectory']==str(release)
    assert value['EnvironmentVariables']['PYTHONPATH']==str(release)
    assert value['StandardErrorPath']==str(private/'https-proxy.log')
    assert 'secret' not in str(value).lower()

def test_supervision_rejects_missing_release(tmp_path):
    with pytest.raises(ValueError,match='DEV_PROXY_LAUNCH_PATH_INVALID'):
        launch_agent(tmp_path/'missing',tmp_path/'python',tmp_path)


def test_preserves_venv_interpreter_symlink(tmp_path):
    release=tmp_path/'release';script=release/'ops/macos/shopping/dev_order_https_proxy.py'
    script.parent.mkdir(parents=True);script.write_text('# fixture')
    base=tmp_path/'base-python';base.write_text('# fixture')
    venv=tmp_path/'venv-python';venv.symlink_to(base)
    private=tmp_path/'private';private.mkdir()
    assert plistlib.loads(launch_agent(release,venv,private))['ProgramArguments'][0]==str(venv)
