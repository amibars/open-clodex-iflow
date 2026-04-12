from pathlib import Path


def test_cli_module_exists():
    cli_path = Path(__file__).resolve().parents[2] / "src" / "open_clodex_iflow" / "cli.py"
    assert cli_path.exists(), "CLI entrypoint must exist at src/open_clodex_iflow/cli.py"


def test_package_init_exists():
    init_path = Path(__file__).resolve().parents[2] / "src" / "open_clodex_iflow" / "__init__.py"
    assert init_path.exists(), "Package init must exist"
