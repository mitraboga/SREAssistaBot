import json
from unittest.mock import MagicMock, patch

import pytest

from agents.sre_agent.sub_agents.kubernetes.tools import kubernetes_tools


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


@pytest.mark.asyncio
async def test_list_contexts_parses_context_names():
    with patch.object(kubernetes_tools.shutil, "which", return_value="kubectl"):
        with patch.object(
            kubernetes_tools.subprocess,
            "run",
            return_value=_completed(stdout="dev\nprod\n"),
        ) as run:
            result = await kubernetes_tools.list_contexts()

    assert result["status"] == "success"
    assert result["contexts"] == ["dev", "prod"]
    assert result["count"] == 2
    run.assert_called_once()


@pytest.mark.asyncio
async def test_list_pods_summarizes_phase_and_restarts():
    payload = {
        "items": [
            {
                "metadata": {
                    "name": "api-1",
                    "namespace": "default",
                    "creationTimestamp": "2026-05-13T00:00:00Z",
                    "labels": {"app": "api"},
                },
                "spec": {"nodeName": "node-a"},
                "status": {
                    "phase": "Running",
                    "podIP": "10.0.0.10",
                    "containerStatuses": [
                        {"ready": True, "restartCount": 1},
                        {"ready": False, "restartCount": 2},
                    ],
                },
            }
        ]
    }

    with patch.object(kubernetes_tools.shutil, "which", return_value="kubectl"):
        with patch.object(
            kubernetes_tools.subprocess,
            "run",
            return_value=_completed(stdout=json.dumps(payload)),
        ):
            result = await kubernetes_tools.list_pods(namespace="default")

    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["phase_counts"] == {"Running": 1}
    assert result["pods"][0]["restart_count"] == 3
    assert result["pods"][0]["containers_ready"] == 1
    assert result["pods"][0]["containers_total"] == 2


@pytest.mark.asyncio
async def test_missing_kubectl_returns_actionable_error():
    with patch.object(kubernetes_tools.shutil, "which", return_value=None):
        result = await kubernetes_tools.list_nodes()

    assert result["status"] == "error"
    assert "kubectl was not found" in result["message"]


@pytest.mark.asyncio
async def test_pod_logs_clamps_tail_lines_and_requires_namespace():
    with patch.object(kubernetes_tools.shutil, "which", return_value="kubectl"):
        with patch.object(
            kubernetes_tools.subprocess,
            "run",
            return_value=_completed(stdout="line 1\nline 2"),
        ) as run:
            result = await kubernetes_tools.get_pod_logs(
                pod_name="api-1",
                namespace="default",
                tail_lines=10_000,
            )

    assert result["status"] == "success"
    assert result["tail_lines"] == 500
    assert "line 1" in result["logs"]
    args = run.call_args.args[0]
    assert "--tail" in args
    assert "500" in args
