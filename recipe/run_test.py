from __future__ import annotations

import os
import re
import socket
import sys
import time

from subprocess import run, PIPE, STDOUT, Popen
from typing import TYPE_CHECKING
from urllib.request import urlopen

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


RE_VERSION = re.escape(os.environ["PKG_VERSION"])

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
        sys.executable,
        "-m",
        "http.server",
        "{port}",
    ]
    proc = Popen(args)
    time.sleep(1)
    yield proc
    proc.terminate()
    proc.wait()


@pytest.fixture
def an_unused_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    sock.close()
    return port


if __name__ == "__main__":
    sys.exit(pytest.main(["-vv", "--tb=long", "--color=yes", __file__]))
