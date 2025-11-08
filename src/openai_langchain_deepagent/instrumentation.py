"""Phoenix instrumentation setup for observability."""

import os
from typing import Optional

from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_phoenix_instrumentation(
    endpoint: Optional[str] = None,
    service_name: str = "openai-langchain-deepagent",
) -> None:
    """
    Set up Phoenix observability instrumentation.

    This configures OpenTelemetry to send traces to Phoenix for monitoring
    LangChain and OpenAI interactions.

    Args:
        endpoint: Phoenix OTLP endpoint (default: http://localhost:4317)
        service_name: Name of the service for trace identification

    Example:
        >>> setup_phoenix_instrumentation()
        >>> # Now all LangChain operations will be traced
    """
    # Use environment variable or default endpoint
    if endpoint is None:
        endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:4317")

    # Check if instrumentation should be enabled
    phoenix_enabled = os.getenv("PHOENIX_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    if not phoenix_enabled:
        print("Phoenix instrumentation is disabled")
        return

    try:
        # Create resource with service name
        resource = Resource(attributes={"service.name": service_name})

        # Set up OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

        # Create tracer provider with batch processor
        tracer_provider = trace_sdk.TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set the tracer provider
        trace_api.set_tracer_provider(tracer_provider)

        # Instrument LangChain
        LangChainInstrumentor().instrument()

        print(f"✓ Phoenix instrumentation enabled: {endpoint}")

    except Exception as e:
        print(f"Warning: Failed to set up Phoenix instrumentation: {e}")
        print("Continuing without observability...")


def is_instrumented() -> bool:
    """
    Check if Phoenix instrumentation is active.

    Returns:
        True if instrumentation is configured and enabled
    """
    phoenix_enabled = os.getenv("PHOENIX_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    return phoenix_enabled and trace_api.get_tracer_provider() is not None
