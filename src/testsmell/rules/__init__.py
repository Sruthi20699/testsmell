"""Importing this package registers every rule module in REGISTRY."""

from . import assertions, structure  # noqa: F401
from .base import REGISTRY, SEVERITY_ORDER, Finding, Rule, Severity

__all__ = ["REGISTRY", "SEVERITY_ORDER", "Finding", "Rule", "Severity"]
