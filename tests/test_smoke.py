"""Agentainer smoke tests.

Run with: pytest tests/ -v
Or:       make test
"""

import shutil
import subprocess
import sys


def test_git_available():
    assert shutil.which("git"), "git not found in PATH"


def test_node_available():
    assert shutil.which("node"), "node not found in PATH"
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.startswith("v")


def test_python3_available():
    assert shutil.which("python3"), "python3 not found in PATH"
    result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
    assert result.returncode == 0


def test_codex_binary_exists():
    codex = shutil.which("codex")
    if codex is None:
        import warnings
        warnings.warn("codex CLI not found (optional)")
    # Not a hard failure: codex is optional


def test_claude_binary_exists():
    claude = shutil.which("claude")
    if claude is None:
        import warnings
        warnings.warn("claude CLI not found (optional, best-effort install)")
    # Not a hard failure: claude install is best-effort


def test_whisper_available():
    assert shutil.which("whisper"), "whisper not found in PATH"


def test_ddgr_available():
    assert shutil.which("ddgr"), "ddgr not found in PATH"


def test_himalaya_available():
    assert shutil.which("himalaya"), "himalaya not found in PATH"
    result = subprocess.run(["himalaya", "--version"], capture_output=True, text=True)
    assert result.returncode == 0


def test_playwright_importable():
    result = subprocess.run(
        [sys.executable, "-c", "import playwright"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"playwright import failed: {result.stderr}"


def test_playwright_fetch_example():
    """Smoke test: fetch example.com with headless Chromium."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from playwright.sync_api import sync_playwright\n"
                "with sync_playwright() as p:\n"
                "    b = p.chromium.launch(headless=True)\n"
                "    page = b.new_page()\n"
                "    page.goto('https://example.com', wait_until='domcontentloaded')\n"
                "    assert 'Example Domain' in page.title()\n"
                "    b.close()\n"
                "print('OK')\n"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"Playwright smoke test failed: {result.stderr}"


def test_agentainer_fetch_script_exists():
    """Verify agentainer-fetch.py exists."""
    from pathlib import Path

    script = Path("/opt/scripts/agentainer-fetch.py")
    if not script.exists():
        # Fallback: check in repo
        script = Path(__file__).parent.parent / "scripts" / "agentainer-fetch.py"
    assert script.exists(), "agentainer-fetch.py not found"


def test_agentainer_run_script_exists():
    """Verify agentainer-run.sh exists."""
    from pathlib import Path

    script = Path("/opt/scripts/agentainer-run.sh")
    if not script.exists():
        script = Path(__file__).parent.parent / "scripts" / "agentainer-run.sh"
    assert script.exists(), "agentainer-run.sh not found"
