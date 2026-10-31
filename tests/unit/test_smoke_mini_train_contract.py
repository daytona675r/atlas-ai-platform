import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[2] / "scripts" / "smoke_mini_train.sh"


def _fake_python(path: Path, *, succeeds: bool) -> None:
    if succeeds:
        body = "#!/usr/bin/env bash\nprintf 'local-run\\n'\nprintf 'model' > model.pkl\n"
    else:
        body = "#!/usr/bin/env bash\necho 'simulated training traceback' >&2\nexit 7\n"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def test_failed_training_cannot_pass_with_stale_artifact(tmp_path: Path) -> None:
    stale = tmp_path / "model.pkl"
    stale.write_bytes(b"stale")
    fake_python = tmp_path / "fake-python"
    _fake_python(fake_python, succeeds=False)

    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=tmp_path,
        env={**os.environ, "PYTHON_BIN": str(fake_python)},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not stale.exists()


def test_successful_training_requires_new_nonempty_artifact(tmp_path: Path) -> None:
    fake_python = tmp_path / "fake-python"
    _fake_python(fake_python, succeeds=True)

    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=tmp_path,
        env={**os.environ, "PYTHON_BIN": str(fake_python)},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "model.pkl").read_bytes() == b"model"
