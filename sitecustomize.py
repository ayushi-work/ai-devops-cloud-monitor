"""
Python 3.9 shim: ensure importlib.metadata exposes packages_distributions
Some libraries expect importlib.metadata.packages_distributions (added in 3.10).
We forward that attribute from the importlib-metadata backport if missing.
"""
try:
    import importlib.metadata as _im_std
    if not hasattr(_im_std, "packages_distributions"):
        try:
            import importlib_metadata as _im_backport  # type: ignore
            _im_std.packages_distributions = _im_backport.packages_distributions  # type: ignore[attr-defined]
        except Exception:
            pass
except Exception:
    # If even stdlib import fails, nothing to do
    pass


