import pytest

from mlops.smoke_validation import select_exact_smoke_run


def run(**overrides):
    value = {
        "id": 1,
        "name": "Smoke CI",
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
    }
    value.update(overrides)
    return value


def test_selects_exact_successful_run() -> None:
    selected = select_exact_smoke_run([run(id=2), run(id=1)], "a" * 40)
    assert selected["id"] == 2


@pytest.mark.parametrize(
    "candidate",
    [
        run(head_sha="b" * 40),
        run(conclusion="failure"),
        run(name="Full Train"),
        run(status="in_progress"),
    ],
)
def test_rejects_non_matching_run(candidate) -> None:
    with pytest.raises(ValueError, match="no successful Smoke CI"):
        select_exact_smoke_run([candidate], "a" * 40)
