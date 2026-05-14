"""
Read-only Kubernetes operations tools.

These tools shell out to kubectl using structured argument lists. They never
invoke a shell and intentionally avoid mutating commands.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from ....utils import get_logger

logger = get_logger(__name__)


def _kubectl_path() -> Optional[str]:
    configured = os.getenv("KUBECTL_PATH")
    if configured:
        return configured
    return shutil.which("kubectl")


def _base_args(context: Optional[str] = None, namespace: Optional[str] = None) -> List[str]:
    kubectl = _kubectl_path()
    if not kubectl:
        raise FileNotFoundError(
            "kubectl was not found on PATH. Install kubectl or set KUBECTL_PATH."
        )

    args = [kubectl]
    kube_context = context or os.getenv("KUBE_CONTEXT")
    if kube_context and kube_context != "your_kube_context":
        args.extend(["--context", kube_context])

    if namespace:
        args.extend(["--namespace", namespace])

    return args


def _kubectl_missing_response(exc: FileNotFoundError) -> Dict[str, Any]:
    return {
        "status": "error",
        "message": str(exc),
        "next_step": "Install kubectl, add it to PATH, or set KUBECTL_PATH in agents/.env.",
    }


def _safe_base_args(
    context: Optional[str] = None, namespace: Optional[str] = None
) -> Dict[str, Any]:
    try:
        return {"status": "success", "args": _base_args(context=context, namespace=namespace)}
    except FileNotFoundError as exc:
        return _kubectl_missing_response(exc)


def _run_kubectl(args: List[str], timeout_seconds: int = 20) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        return {"status": "error", "message": str(exc)}
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": f"kubectl command timed out after {timeout_seconds}s",
            "command": _redact_command(args),
        }
    except Exception as exc:
        logger.error(f"kubectl command failed unexpectedly: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc), "command": _redact_command(args)}

    if completed.returncode != 0:
        return {
            "status": "error",
            "message": completed.stderr.strip() or completed.stdout.strip(),
            "returncode": completed.returncode,
            "command": _redact_command(args),
        }

    return {
        "status": "success",
        "stdout": completed.stdout.strip(),
        "command": _redact_command(args),
    }


def _run_kubectl_json(args: List[str], timeout_seconds: int = 20) -> Dict[str, Any]:
    result = _run_kubectl(args, timeout_seconds=timeout_seconds)
    if result.get("status") != "success":
        return result

    try:
        result["data"] = json.loads(result.get("stdout") or "{}")
        result.pop("stdout", None)
        return result
    except json.JSONDecodeError as exc:
        return {
            "status": "error",
            "message": f"kubectl returned invalid JSON: {exc}",
            "command": result.get("command"),
        }


def _redact_command(args: List[str]) -> str:
    # Context and namespace are not secrets, but avoid exposing full absolute
    # kubectl paths in model-visible output.
    if not args:
        return ""
    display = ["kubectl", *args[1:]]
    return " ".join(display)


def _metadata(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = item.get("metadata", {})
    return {
        "name": metadata.get("name"),
        "namespace": metadata.get("namespace"),
        "creation_timestamp": metadata.get("creationTimestamp"),
        "labels": metadata.get("labels", {}),
    }


async def get_current_context() -> Dict[str, Any]:
    """Return the active kubectl context."""
    base = _safe_base_args()
    if base.get("status") != "success":
        return base

    args = base["args"] + ["config", "current-context"]
    result = _run_kubectl(args, timeout_seconds=10)
    if result.get("status") == "success":
        result["context"] = result.pop("stdout", "")
    return result


async def list_contexts() -> Dict[str, Any]:
    """List available kubectl contexts."""
    base = _safe_base_args()
    if base.get("status") != "success":
        return base

    args = base["args"] + ["config", "get-contexts", "-o", "name"]
    result = _run_kubectl(args, timeout_seconds=10)
    if result.get("status") == "success":
        contexts = [line.strip() for line in result.pop("stdout", "").splitlines() if line.strip()]
        result["contexts"] = contexts
        result["count"] = len(contexts)
    return result


async def list_nodes(context: Optional[str] = None) -> Dict[str, Any]:
    """List Kubernetes nodes and summarize readiness."""
    base = _safe_base_args(context=context)
    if base.get("status") != "success":
        return base

    args = base["args"] + ["get", "nodes", "-o", "json"]
    result = _run_kubectl_json(args)
    if result.get("status") != "success":
        return result

    nodes = []
    for item in result["data"].get("items", []):
        status = item.get("status", {})
        conditions = status.get("conditions", [])
        ready_condition = next((c for c in conditions if c.get("type") == "Ready"), {})
        nodes.append(
            {
                **_metadata(item),
                "ready": ready_condition.get("status") == "True",
                "ready_reason": ready_condition.get("reason"),
                "roles": item.get("metadata", {}).get("labels", {}),
                "capacity": status.get("capacity", {}),
                "allocatable": status.get("allocatable", {}),
            }
        )

    result.pop("data", None)
    result["nodes"] = nodes
    result["count"] = len(nodes)
    result["ready_count"] = sum(1 for node in nodes if node["ready"])
    return result


async def list_pods(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """List pods by namespace or across all namespaces if none is provided."""
    base = _safe_base_args(context=context, namespace=namespace)
    if base.get("status") != "success":
        return base

    args = base["args"]
    args.extend(["get", "pods"])
    if namespace is None:
        args.append("--all-namespaces")
    if label_selector:
        args.extend(["--selector", label_selector])
    args.extend(["-o", "json"])

    result = _run_kubectl_json(args)
    if result.get("status") != "success":
        return result

    pods = []
    for item in result["data"].get("items", []):
        status = item.get("status", {})
        container_statuses = status.get("containerStatuses", [])
        pods.append(
            {
                **_metadata(item),
                "phase": status.get("phase"),
                "pod_ip": status.get("podIP"),
                "node_name": status.get("hostIP") or item.get("spec", {}).get("nodeName"),
                "restart_count": sum(cs.get("restartCount", 0) for cs in container_statuses),
                "containers_ready": sum(1 for cs in container_statuses if cs.get("ready")),
                "containers_total": len(container_statuses),
            }
        )

    result.pop("data", None)
    result["pods"] = pods
    result["count"] = len(pods)
    result["namespace"] = namespace or "all"
    result["phase_counts"] = _count_by_key(pods, "phase")
    return result


async def list_deployments(
    namespace: Optional[str] = None,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """List deployments and rollout replica health."""
    base = _safe_base_args(context=context, namespace=namespace)
    if base.get("status") != "success":
        return base

    args = base["args"]
    args.extend(["get", "deployments"])
    if namespace is None:
        args.append("--all-namespaces")
    args.extend(["-o", "json"])

    result = _run_kubectl_json(args)
    if result.get("status") != "success":
        return result

    deployments = []
    for item in result["data"].get("items", []):
        spec = item.get("spec", {})
        status = item.get("status", {})
        deployments.append(
            {
                **_metadata(item),
                "desired_replicas": spec.get("replicas", 0),
                "ready_replicas": status.get("readyReplicas", 0),
                "available_replicas": status.get("availableReplicas", 0),
                "updated_replicas": status.get("updatedReplicas", 0),
            }
        )

    result.pop("data", None)
    result["deployments"] = deployments
    result["count"] = len(deployments)
    result["namespace"] = namespace or "all"
    return result


async def list_services(
    namespace: Optional[str] = None,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """List Kubernetes services."""
    base = _safe_base_args(context=context, namespace=namespace)
    if base.get("status") != "success":
        return base

    args = base["args"]
    args.extend(["get", "services"])
    if namespace is None:
        args.append("--all-namespaces")
    args.extend(["-o", "json"])

    result = _run_kubectl_json(args)
    if result.get("status") != "success":
        return result

    services = []
    for item in result["data"].get("items", []):
        spec = item.get("spec", {})
        services.append(
            {
                **_metadata(item),
                "type": spec.get("type"),
                "cluster_ip": spec.get("clusterIP"),
                "ports": spec.get("ports", []),
                "selector": spec.get("selector", {}),
            }
        )

    result.pop("data", None)
    result["services"] = services
    result["count"] = len(services)
    result["namespace"] = namespace or "all"
    return result


async def get_pod_logs(
    pod_name: str,
    namespace: str,
    container: Optional[str] = None,
    tail_lines: int = 100,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch recent logs for one pod. This is read-only but may contain sensitive data."""
    if not pod_name or not namespace:
        return {"status": "error", "message": "pod_name and namespace are required"}

    safe_tail = max(1, min(int(tail_lines), 500))
    base = _safe_base_args(context=context, namespace=namespace)
    if base.get("status") != "success":
        return base

    args = base["args"]
    args.extend(["logs", pod_name, "--tail", str(safe_tail)])
    if container:
        args.extend(["--container", container])

    result = _run_kubectl(args, timeout_seconds=30)
    if result.get("status") == "success":
        result["pod_name"] = pod_name
        result["namespace"] = namespace
        result["tail_lines"] = safe_tail
        result["logs"] = result.pop("stdout", "")
        result["warning"] = "Logs are raw application output and may contain sensitive data."
    return result


async def get_cluster_summary(
    namespace: Optional[str] = None,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a compact read-only summary of nodes, pods, deployments, and services."""
    nodes = await list_nodes(context=context)
    pods = await list_pods(namespace=namespace, context=context)
    deployments = await list_deployments(namespace=namespace, context=context)
    services = await list_services(namespace=namespace, context=context)

    return {
        "status": "success"
        if all(
            section.get("status") == "success" for section in [nodes, pods, deployments, services]
        )
        else "partial",
        "namespace": namespace or "all",
        "nodes": {
            "status": nodes.get("status"),
            "count": nodes.get("count"),
            "ready_count": nodes.get("ready_count"),
            "message": nodes.get("message"),
        },
        "pods": {
            "status": pods.get("status"),
            "count": pods.get("count"),
            "phase_counts": pods.get("phase_counts"),
            "message": pods.get("message"),
        },
        "deployments": {
            "status": deployments.get("status"),
            "count": deployments.get("count"),
            "message": deployments.get("message"),
        },
        "services": {
            "status": services.get("status"),
            "count": services.get("count"),
            "message": services.get("message"),
        },
    }


def _count_by_key(items: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
