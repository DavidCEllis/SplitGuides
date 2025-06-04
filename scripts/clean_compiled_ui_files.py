import shutil
from pathlib import Path


def clean_built_ui():
    pth = Path(__file__).parents[1] / "src" / "splitguides" / "ui" / "layouts" / "build"
    shutil.rmtree(pth)

if __name__ == "__main__":
    clean_built_ui()
