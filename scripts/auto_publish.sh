#!/bin/bash
# Auto-publish wrapper (bash fallback if python not available)
set -e
REPO="sendescapade456-svg/convacationgamesimagesvideoscriptgenerator"
for f in cgames.html index.html glimmer.html; do
  [ -f "$f" ] || continue
  echo "Checking $f..."
  python3 scripts/auto_publish.py 2>&1 | head -n 50
  break
done
