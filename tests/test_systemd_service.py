from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_TEMPLATE = REPO_ROOT / "deploy" / "chathexo.service"


def test_systemd_service_runs_chathexo_from_repository():
    content = SERVICE_TEMPLATE.read_text(encoding="utf-8")

    assert "WorkingDirectory=/home/tianlejin/myblog/chathexo-server" in content
    assert "ExecStart=/home/tianlejin/.local/bin/uv run python -m chathexo.main" in content


def test_systemd_service_is_resilient_and_logs_to_journald():
    content = SERVICE_TEMPLATE.read_text(encoding="utf-8")

    assert "Restart=on-failure" in content
    assert "RestartSec=5" in content
    assert "StandardOutput=journal" in content
    assert "StandardError=journal" in content
    assert "WantedBy=default.target" in content
