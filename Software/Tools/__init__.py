# Software/Tools/__init__.py
"""
Tools Layer (Development Utilities)

This package contains optional development utilities such as:
    - debug video viewers,
    - visualization helpers,
    - profiling tools,
    - diagnostic scripts.

These tools are NOT part of the production system.
They must not be imported by the App, Control, Service, Interface, or Drivers layers.

They exist purely to assist developers during testing and debugging.

Example (development only):
    from Software.Tools.debug_display import main
    main()
"""

# Tools are intentionally not exported in __all__.
# They should be imported explicitly by developers.
__all__: list[str] = []