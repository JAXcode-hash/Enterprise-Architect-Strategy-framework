"""Enterprise Architect Strategy framework.

A repeatable, partitioned method for standing up an architecture direction:
nine cyber-security validator domains each offer defensible options, and an
orchestrator interrogates those options against each other to produce a
coherent end-to-end position, a graded verdict, and three levels of output.

Stdlib only. Every request gets its own isolated project.
"""

from .projects import ENGINE_VERSION as __version__  # noqa: F401
