import hashlib

import pytest

from mlops.candidate_validation import validate_candidate

RUN = {
    "id": 42,
    "name": "Full Train",
    "status": "completed",
    "conclusion": "success",
    "head_sha": "a" * 40,
}


def metadata(model: bytes = b"model") -> dict[str, str]:
    return {
        "source_run_id": "42",
        "source_workflow": "Full Train",
        "commit_sha": "a" * 40,
        "run_id": "mlflow-run-1",
        "model_sha256": hashlib.sha256(model).hexdigest(),
    }


def test_exact_successful_candidate_is_accepted() -> None:
    validate_candidate(RUN, metadata(), b"model", "42")


@pytest.mark.parametrize(
    "changed_run, requested, message",
    [
        ({**RUN, "name": "Smoke CI"}, "42", "Full Train"),
        ({**RUN, "conclusion": "failure"}, "42", "successful"),
        ({**RUN, "id": 99}, "42", "run ID"),
        ({**RUN, "head_sha": "b" * 40}, "42", "head SHA"),
    ],
)
def test_candidate_rejects_wrong_provenance(changed_run, requested, message) -> None:
    with pytest.raises(ValueError, match=message):
        validate_candidate(changed_run, metadata(), b"model", requested)


def test_candidate_rejects_hash_mismatch() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        validate_candidate(RUN, metadata(), b"tampered", "42")
