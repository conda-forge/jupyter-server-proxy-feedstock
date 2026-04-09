import os
from subprocess import run, PIPE, STDOUT, Popen
import pytest
import socket
from urllib.request import urlopen
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


PKG_VERSION = os.environ["PKG_VERSION"]
RE_VERSION = re.escape(PKG_VERSION)

SCRIPTS = {
    rf"jupyter_server_proxy\s*{RE_VERSION}": ["pip", "list"],
    rf"@jupyterhub/jupyter-server-proxy.*{RE_VERSION}.*OK": [
        "jupyter",
        "labextension",
        "list",
    ],
    r"jupyter_server_proxy.*OK": ["jupyter", "server", "extension", "list"],
    r"Usage: jupyter standaloneproxy": ["jupyter-standaloneproxy", "--help"],
}


@pytest.mark.parametrize(("pattern", "args"), [*SCRIPTS.items()])
def test_script_pattern(pattern: str, args: list[str]) -> None:
    res = run(args, stdout=PIPE, stderr=STDOUT, encoding="utf-8")
    print(res.stdout)
    assert re.search(pattern, res.stdout)


def test_proxy_cli(a_proxied_server: Popen, an_unused_port: int) -> None:
    with urlopen(f"http://127.0.0.1:{an_unused_port}") as fp:
        assert "Directory listing for" in fp.read().decode("utf-8")


@pytest.fixture
def a_proxied_server(an_unused_port: int) -> Iterator[Popen]:
    args = [
        "jupyter-standaloneproxy",
        "--no-authentication",
        f"--port={an_unused_port}",
        "--",
        "python",
        "-mhttp.server",
        "{port}",
    ]
    proc = Popen(args)
    yield proc
    proc.terminate()


@pytest.fixture
def an_unused_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    sock.close()
    return port
