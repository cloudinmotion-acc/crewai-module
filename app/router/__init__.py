"""Minimal router package used by local development and testing.

The full runtime provides a richer `app.router` package; this
lightweight version supplies a `ModelRouterClient` stub so the
crewai-module can run standalone.
"""

__all__ = ["client"]
