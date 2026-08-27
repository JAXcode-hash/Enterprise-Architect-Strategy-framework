"""Output renderers.

Three levels of detail, from the same reconciled base plate:

  lld       one low-level design per domain - the detail an engineer builds from
  hld       one end-to-end design - scope, flow, boundaries, connectivity
  exec_pack one executive pack - what it buys, what it costs, what could go wrong

Plus `baseplate`, which is the framework's own section 7 artefact, and `html`,
a self-contained dashboard for the project.
"""

from . import baseplate, exec_pack, hld, html, lld, options  # noqa: F401
