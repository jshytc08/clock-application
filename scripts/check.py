"""Run the local release gate. Any failed command stops the gate."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
npm = shutil.which("npm")
node = shutil.which("node")
if not npm or not node:
    raise SystemExit("Install Node.js 22+ and run npm ci before running checks.")

commands = [
    [sys.executable, "-m", "pip", "check"],
    [sys.executable, "-m", "ruff", "check", "app", "tests", "scripts"],
    [sys.executable, "-m", "ruff", "format", "--check", "app", "tests", "scripts"],
    [node, "--check", "app/static/js/main.js"],
    [node, "--check", "app/static/js/core.mjs"],
    [npm, "run", "format:check"],
    [npm, "test"],
    [sys.executable, "-m", "pytest", "-q"],
    ["git", "diff", "--check"],
]
for command in commands:
    print("\nRunning: " + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
print("\nAll release checks passed. Browser screenshots are in artifacts/.")
