name: Testing

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ 3.10 ]
    continue-on-error: false

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          sudo apt-get update
          python -m pip install --upgrade pip
          python -m pip install --upgrade pip-tools
          make venv
      - uses: actions/cache@v2
        id: cache-venv
        with:
          path: ./.venv/  # we cache: the virtualenv
          # The cache key depends on requirements*.txt
          key: v4-${{ runner.os }}-${{ matrix.python-version }}-venv-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            v4-${{ runner.os }}-${{ matrix.python-version }}-venv-
      # Build a virtualenv, but only if it doesn't already exist
      - name: Make venv
        run: make venv
        if: steps.cache-venv.outputs.cache-hit != 'true'
      - name: Sync dependencies
        run: make pip-sync-dev
      - name: Check linting
        run: make lint
      - name: Testing
        run: make test
