from pathlib import Path
Path.ls = lambda x: list(x.iterdir())
