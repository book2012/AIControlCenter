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
