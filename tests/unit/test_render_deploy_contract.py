from pathlib import Path

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "deploy.yml"


def test_deploy_uses_render_release_handoff_and_fails_closed() -> None:
    workflow = WORKFLOW.read_text()
    assert "RENDER_SERVICE_URL" in workflow
    assert "RENDER_DEPLOY_HOOK" in workflow
    assert "render-release" in workflow
    assert "contents: write" in workflow
    assert "git push --force-with-lease" in workflow
    assert 'curl --fail --silent --show-error --request POST "$RENDER_DEPLOY_HOOK"' in workflow
    assert "Deployment skipped" not in workflow
    assert "HF_SPACE" not in workflow
    assert "huggingface" not in workflow.lower()


def test_hosted_verification_checks_readiness_and_candidate_identity() -> None:
    workflow = WORKFLOW.read_text()
    assert 'export SERVE_URL="${RENDER_SERVICE_URL%/}"' in workflow
    assert '[[ "$ready" == true ]]' in workflow
    assert "scripts/verify_deploy.py" in workflow
    for variable in (
        "EXPECTED_COMMIT_SHA",
        "EXPECTED_SOURCE_RUN_ID",
        "EXPECTED_MLFLOW_RUN_ID",
        "EXPECTED_MODEL_SHA256",
    ):
        assert variable in workflow
