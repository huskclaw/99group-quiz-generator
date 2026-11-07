"""Run current bilingual integration cases sequentially against the local model."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
for case in ('indonesian', 'english', 'long-notes', 'fun'):
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify_bilingual.py'), '--case', case], cwd=ROOT, check=True)
