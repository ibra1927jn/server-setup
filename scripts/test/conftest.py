import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add scripts/ directory to path so shared_config can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))


def mock_ssh(stdout="", stderr=""):
    """Create a mock SSH client that returns given stdout/stderr."""
    ssh = MagicMock()
    o = MagicMock()
    o.read.return_value = stdout.encode()
    e = MagicMock()
    e.read.return_value = stderr.encode()
    ssh.exec_command.return_value = (MagicMock(), o, e)
    return ssh
