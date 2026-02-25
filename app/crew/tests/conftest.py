import sys
from pathlib import Path

# ensure that the "app" directory is on sys.path so that the `crew` package
# can be imported when tests are executed from the repository root.
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
