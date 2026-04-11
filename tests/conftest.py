import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_script_path = Path(__file__).parent.parent / "nhse-jira"
_loader = importlib.machinery.SourceFileLoader("nhse_jira", str(_script_path))
_spec = importlib.util.spec_from_file_location("nhse_jira", _script_path, loader=_loader)
nhse_jira = importlib.util.module_from_spec(_spec)
sys.modules["nhse_jira"] = nhse_jira
_spec.loader.exec_module(nhse_jira)
