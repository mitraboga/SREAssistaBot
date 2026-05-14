"""
Shared utility functions for the SRE agent and sub-agents.
"""

import os
import logging
import sys
import re
from typing import Optional


class ModelConfigurationError(Exception):
    """Raised when model configuration fails."""

    pass


# ----------------------------
# Logging helpers
# ----------------------------
_SECRET_PATTERNS = [
    # AWS access keys (very rough patterns)
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    # Common "key=" / "token=" patterns
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*=\s*['\"]?([^\s'\"\\]+)"),
]


def redact_secrets(text: str) -> str:
    """
    Best-effort secret redaction for logs.
    This is intentionally conservative (won't catch everything),
    but it reduces accidental credential leakage.
    """
    if not text:
        return text

    redacted = text

    # Replace AWS key-like patterns
    for pat in _SECRET_PATTERNS:
        redacted = pat.sub(
            lambda m: m.group(0).split("=")[0] + "=***" if "=" in m.group(0) else "***REDACTED***",
            redacted,
        )

    # Also explicitly redact common env values if present
    for env_key in [
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
    ]:
        v = os.getenv(env_key)
        if v and v in redacted:
            redacted = redacted.replace(v, "***REDACTED***")

    return redacted


def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    include_timestamp: bool = True,
    include_module: bool = True,
) -> logging.Logger:
    """
    Set up a standardized logger for SRE bot modules.

    - Uses LOG_LEVEL env var (default INFO)
    - Prevents duplicate handlers
    - Can optionally include timestamp + module name in logs

    NOTE: This function keeps the existing behavior used by your MVP.
    """
    logger = logging.getLogger(name)

    # If already configured, keep it stable (prevents duplicate logs)
    if logger.handlers:
        return logger

    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    try:
        log_level = getattr(logging, level)
    except AttributeError:
        log_level = logging.INFO
        print(f"Warning: Invalid log level '{level}', defaulting to INFO", file=sys.stderr)

    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if format_string is None:
        parts = []
        if include_timestamp:
            parts.append("%(asctime)s")
        parts.append("%(levelname)s")
        if include_module:
            parts.append("%(name)s")
        parts.append("%(message)s")
        format_string = " - ".join(parts)

    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper for standard logger setup."""
    return setup_logger(name)


logger = get_logger(__name__)


def _getenv_exact(key: str, default: str | None = None) -> str | None:
    """Read an environment variable only when the exact key spelling exists."""
    for env_key, value in os.environ.items():
        if env_key == key:
            return value
    return default


def load_instruction_from_file(file_path: str) -> str:
    """
    Load instruction text from a markdown file.
    Used by agents to load system prompts from external markdown.
    """
    try:
        if not os.path.exists(file_path):
            error_msg = f"Instruction file not found: {file_path}"
            logger.error(error_msg)
            return error_msg

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            warning_msg = f"Instruction file is empty: {file_path}"
            logger.warning(warning_msg)
            return warning_msg

        logger.debug(f"Successfully loaded instruction from {file_path}")
        return content

    except Exception as e:
        error_msg = f"Error loading instruction file {file_path}: {e}"
        logger.error(error_msg)
        return error_msg


# ----------------------------
# Model selection
# ----------------------------
def get_configured_model():
    """
    Determine model configuration based on available API keys.
    Priority (default): Google > Anthropic > Bedrock

    Optional override:
      MODEL_PROVIDER=google|anthropic|bedrock|ollama
    """
    logger = get_logger(__name__)

    # Test/CI environment shortcut (keeps your existing intent)
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("CI"):
        google_key = _getenv_exact("GOOGLE_API_KEY")
        anthropic_key = _getenv_exact("ANTHROPIC_API_KEY")

        if google_key and google_key.strip():
            model = _getenv_exact("GOOGLE_AI_MODEL", "gemini-2.0-flash")
            logger.info(f"🧪 Test/CI environment: Using Google Gemini model: {model}")
            return model

        if anthropic_key and anthropic_key.strip():
            model_name = _getenv_exact("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
            litellm_model_name = (
                model_name if model_name.startswith("anthropic/") else f"anthropic/{model_name}"
            )
            logger.info(f"🧪 Test/CI environment: Using mock Claude model: {model_name}")
            try:
                from google.adk.models.lite_llm import LiteLlm

                return LiteLlm(model=litellm_model_name)
            except ImportError:

                class MockLiteLlm:
                    def __init__(self, model):
                        self.model = model

                return MockLiteLlm(model=litellm_model_name)

    provider_override = (_getenv_exact("MODEL_PROVIDER", "") or "").strip().lower()
    if provider_override not in {"", "google", "anthropic", "bedrock", "ollama"}:
        logger.warning(f"Unknown MODEL_PROVIDER='{provider_override}'. Ignoring override.")
        provider_override = ""

    def try_google():
        google_key = _getenv_exact("GOOGLE_API_KEY")
        if google_key and google_key.strip():
            model = _getenv_exact("GOOGLE_AI_MODEL", "gemini-2.0-flash")
            logger.info(f"Using Google Gemini provider with model: {model}")
            logger.info("GOOGLE_API_KEY found and validated")
            return model
        return None

    def try_anthropic():
        anthropic_key = _getenv_exact("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key.strip():
            try:
                from google.adk.models.lite_llm import LiteLlm
            except ImportError as e:
                logger.error(f"Failed to import LiteLlm: {e}")
                raise ModelConfigurationError(
                    "LiteLlm is required for Anthropic Claude. Please ensure google-adk is properly installed."
                )

            model_name = _getenv_exact("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
            litellm_model_name = (
                model_name if model_name.startswith("anthropic/") else f"anthropic/{model_name}"
            )
            logger.info(f"Using Anthropic Claude provider with model: {model_name}")
            logger.info("ANTHROPIC_API_KEY found and validated")
            return LiteLlm(model=litellm_model_name)
        return None

    def try_bedrock():
        bedrock_model_id = _getenv_exact("BEDROCK_MODEL_ID") or _getenv_exact(
            "BEDROCK_INFERENCE_PROFILE"
        )
        if bedrock_model_id and bedrock_model_id.strip():
            bedrock_api_key = _getenv_exact("AWS_BEARER_TOKEN_BEDROCK") or _getenv_exact(
                "BEDROCK_API_KEY"
            )
            if bedrock_api_key and bedrock_api_key.strip():
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bedrock_api_key.strip()

            try:
                import boto3  # noqa: F401
            except ImportError:
                logger.error("AWS Bedrock configuration error: boto3 is required but not installed")
                raise ModelConfigurationError(
                    "Bedrock requires boto3. Install with: pip install boto3"
                )

            # LiteLLM expects AWS_REGION_NAME; keep AWS_REGION as the friendly project env.
            aws_region = (
                _getenv_exact("AWS_REGION_NAME")
                or _getenv_exact("BEDROCK_REGION")
                or _getenv_exact("AWS_REGION")
                or _getenv_exact("AWS_DEFAULT_REGION")
            )
            if aws_region:
                os.environ["AWS_REGION_NAME"] = aws_region
                os.environ.setdefault("AWS_DEFAULT_REGION", aws_region)

            # Bedrock API keys are service-scoped bearer tokens and do not support STS.
            # If no Bedrock API key is present, validate normal AWS credentials quickly
            # without invoking a billable Bedrock model.
            if bedrock_api_key and bedrock_api_key.strip():
                logger.info("Using Amazon Bedrock API key authentication")
            else:
                try:
                    import boto3

                    sts = boto3.client("sts")
                    identity = sts.get_caller_identity()
                    logger.info(f"AWS credentials validated for account: {identity['Account']}")
                except Exception as e:
                    logger.error("AWS Bedrock configuration error: AWS credentials not configured")
                    logger.error(f"   Error details: {str(e)}")
                    raise ModelConfigurationError(
                        "Bedrock requires either BEDROCK_API_KEY/AWS_BEARER_TOKEN_BEDROCK "
                        "or valid AWS credentials."
                    )

            try:
                from google.adk.models.lite_llm import LiteLlm
            except ImportError as e:
                logger.error(f"Failed to import LiteLlm: {e}")
                raise ModelConfigurationError(
                    "LiteLlm is required for AWS Bedrock. Please ensure google-adk is properly installed."
                )

            bedrock_model_id = bedrock_model_id.strip()
            bedrock_model = (
                bedrock_model_id
                if bedrock_model_id.startswith("bedrock/")
                else f"bedrock/{bedrock_model_id}"
            )
            logger.info(f"Using AWS Bedrock provider with model: {bedrock_model_id}")
            logger.info(f"LiteLLM model configured as: {bedrock_model}")
            return LiteLlm(model=bedrock_model)
        return None

    def try_ollama():
        try:
            from google.adk.models.lite_llm import LiteLlm
        except ImportError as e:
            logger.error(f"Failed to import LiteLlm: {e}")
            raise ModelConfigurationError(
                "LiteLlm is required for Ollama. Please ensure google-adk is properly installed."
            )

        model_name = _getenv_exact("OLLAMA_MODEL", "qwen3.5:latest")
        litellm_model_name = (
            model_name if model_name.startswith("ollama/") else f"ollama/{model_name}"
        )
        api_base = _getenv_exact("OLLAMA_API_BASE")
        if api_base and "host.docker.internal" in api_base and not os.path.exists("/.dockerenv"):
            api_base = api_base.replace("host.docker.internal", "localhost")
        if api_base:
            os.environ["OLLAMA_API_BASE"] = api_base

        logger.info(
            f"Using Ollama local provider with model: {litellm_model_name}, api_base={api_base}"
        )
        return LiteLlm(model=litellm_model_name)

    # Apply override order if requested
    if provider_override == "google":
        model = try_google()
        if model is not None:
            return model
    elif provider_override == "anthropic":
        model = try_anthropic()
        if model is not None:
            return model
    elif provider_override == "bedrock":
        model = try_bedrock()
        if model is not None:
            return model
        raise ModelConfigurationError(
            "MODEL_PROVIDER=bedrock requires BEDROCK_MODEL_ID or BEDROCK_INFERENCE_PROFILE."
        )
    elif provider_override == "ollama":
        return try_ollama()

    # Default priority order (unchanged)
    model = try_google()
    if model is not None:
        return model

    model = try_anthropic()
    if model is not None:
        return model

    model = try_bedrock()
    if model is not None:
        return model

    # No valid configuration found
    logger.error("No AI provider configured!")
    logger.error(
        "Configure one of: GOOGLE_API_KEY, ANTHROPIC_API_KEY, BEDROCK_INFERENCE_PROFILE, or MODEL_PROVIDER=ollama"
    )
    logger.error("Optional override: MODEL_PROVIDER=google|anthropic|bedrock|ollama")

    raise ModelConfigurationError(
        "No AI provider API key found. Please set GOOGLE_API_KEY, "
        "ANTHROPIC_API_KEY, or BEDROCK_INFERENCE_PROFILE."
    )
