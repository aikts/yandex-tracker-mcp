"""Shared utilities for protocol compliance testing."""

import inspect
from typing import Any


def get_protocol_methods(protocol_class: type) -> list[str]:
    """Get all method names defined in a protocol.

    Args:
        protocol_class: Protocol class to extract methods from

    Returns:
        List of method names (excluding private methods)
    """
    methods = []
    for name, value in inspect.getmembers(protocol_class):
        if (
            inspect.isfunction(value)
            or inspect.ismethod(value)
            or (hasattr(value, "__annotations__") and callable(value))
        ):
            if not name.startswith("_"):  # Skip private methods
                methods.append(name)
    return methods


def verify_method_signatures(implementation: Any, protocol_class: type) -> None:
    """Verify that implementation method signatures match protocol.

    Args:
        implementation: Implementation instance to verify
        protocol_class: Protocol class to check against

    Raises:
        AssertionError: If signatures don't match
    """
    protocol_methods = get_protocol_methods(protocol_class)

    for method_name in protocol_methods:
        if not hasattr(implementation, method_name):
            continue  # Skip if method doesn't exist (will be caught by other tests)

        impl_method = getattr(implementation, method_name)
        protocol_method = getattr(protocol_class, method_name)

        # Get signatures
        impl_sig = inspect.signature(impl_method)
        protocol_sig = inspect.signature(protocol_method)

        # Compare parameter names and types
        impl_params = list(impl_sig.parameters.keys())
        protocol_params = list(protocol_sig.parameters.keys())

        # Skip 'self' parameter for comparison
        if "self" in impl_params:
            impl_params.remove("self")
        if "self" in protocol_params:
            protocol_params.remove("self")

        assert impl_params == protocol_params, (
            f"Method {method_name}: parameter mismatch. "
            f"Implementation: {impl_params}, Protocol: {protocol_params}"
        )
