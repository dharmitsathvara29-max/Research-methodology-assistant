"""Streamlit Community Cloud entrypoint wrapper.
Directs Streamlit Cloud to the main MethodWise multi-page app.py orchestrator.
"""

import os
import sys
import runpy

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    runpy.run_path(os.path.join(PROJECT_ROOT, "app.py"), run_name="__main__")
else:
    # When Streamlit executes the file in its execution runner
    runpy.run_path(os.path.join(PROJECT_ROOT, "app.py"), run_name="__main__")
