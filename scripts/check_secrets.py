"""Fail CI if a local environment file or obvious key is tracked."""

import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')

for name in filter(None, tracked):
    path = pathlib.PurePosixPath(name)
    if path.name.startswith('.env') and path.name != '.env.example':
        print(f'Tracked environment file: {name}', file=sys.stderr)
        sys.exit(1)
    if path.suffix not in {'.py', '.js', '.ts', '.tsx', '.json'}:
        continue
    content = (root / name).read_text(encoding='utf-8', errors='ignore')
    if re.search(r'AIza[0-9A-Za-z_-]{30,}', content):
        print(f'Credential-like value in: {name}', file=sys.stderr)
        sys.exit(1)
    if re.search(r'(?m)^\s*NEXT_PUBLIC_CANVAS_TOKEN\s*=\s*[^\s#]+', content):
        print(f'Public Canvas token assignment in: {name}', file=sys.stderr)
        sys.exit(1)

print('Tracked env and key checks passed.')
