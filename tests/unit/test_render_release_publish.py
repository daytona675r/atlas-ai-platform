import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "publish_render_release.sh"


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def test_publish_force_adds_ignored_model_and_metadata_to_release_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    git("config", "user.name", "test", cwd=repo)
    git("config", "user.email", "test@example.invalid", cwd=repo)
    (repo / ".gitignore").write_text("model.pkl\n", encoding="utf-8")
    (repo / "README.md").write_text("source\n", encoding="utf-8")
    git("add", ".gitignore", "README.md", cwd=repo)
    git("commit", "-m", "source", cwd=repo)
    source_sha = git("rev-parse", "HEAD", cwd=repo)
    git("remote", "add", "origin", str(remote), cwd=repo)
    git("push", "origin", "HEAD:refs/heads/main", cwd=repo)
    git("push", "origin", "HEAD:refs/heads/render-release", cwd=repo)

    (repo / "model.pkl").write_bytes(b"verified model")
    (repo / "candidate-metadata.json").write_text('{"model_sha256":"verified"}\n', encoding="utf-8")
    subprocess.run(
        ["bash", str(SCRIPT), "render-release", source_sha],
        cwd=repo,
        env={**os.environ, "GIT_REMOTE": "origin"},
        check=True,
        capture_output=True,
        text=True,
    )

    assert git("--git-dir", str(remote), "show", "refs/heads/render-release:model.pkl", cwd=repo)
    assert git(
        "--git-dir",
        str(remote),
        "show",
        "refs/heads/render-release:candidate-metadata.json",
        cwd=repo,
    )
