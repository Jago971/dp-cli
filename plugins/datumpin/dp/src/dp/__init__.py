"""dp: the datumpin plugin's command line."""
from importlib.resources import files
from pathlib import Path


def data(*parts):
    """A flow-map or skill file: packaged in `dp/data`, else the plugin's own in a source checkout.

    The fallback applies only where `pyproject.toml` sits above `src/`, so
    an installed dp never reads a stray folder beside site-packages.
    """
    packaged = files("dp") / "data"
    if packaged.is_dir():
        return packaged.joinpath(*parts)
    here = Path(__file__).resolve()
    if (here.parents[2] / "pyproject.toml").is_file():
        return here.parents[3].joinpath(*parts)
    return packaged.joinpath(*parts)
