def test_deliberate_failure():
    """Made by `make demo-fail`: this MUST fail so the pipeline stops before deploy."""
    assert 1 + 1 == 3
