import sys
from pathlib import Path

# Add scripts/ directory to path so shared_config can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
