"""Layer 1 inspection adapters.

Adapters convert an external inspector's output into typed intermediates. They never
raise to their caller and never return partially-parsed data without saying so.
"""
