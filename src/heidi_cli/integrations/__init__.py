"""
Integrations module for Heidi CLI.

This module provides integrations with external services and platforms
such as HuggingFace Hub for model discovery and download.
"""

from .huggingface import HuggingFaceIntegration, huggingface_integration

__all__ = ["HuggingFaceIntegration", "huggingface_integration"]
