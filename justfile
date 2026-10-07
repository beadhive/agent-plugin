# Preparation checks do not establish public artifact acceptance.
check:
    uv sync --locked
    uv run --locked python -m unittest discover -s tests -v
    uv run --locked python qa/check_stage.py

# Public CI always requires the actual generated artifact and immutable sidecar.
accept:
    uv run --locked python qa/check_artifact.py --artifact . --receipt release-receipt.json --destination --require-artifact
