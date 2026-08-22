# sources/__init__.py
import pkgutil, importlib
from pathlib import Path

for mod in pkgutil.iter_modules([str(Path(__file__).parent)]):
    importlib.import_module(f"sources.{mod.name}")
