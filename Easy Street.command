#!/bin/bash
cd "$(dirname "$0")" || exit 1
if command -v python3.12 >/dev/null 2>&1; then
  python3.12 launch.py
else
  python3 launch.py
fi
result=$?
if [ "$result" -ne 0 ]; then
  echo "Install Python 3.12 from https://www.python.org/downloads/ if it is missing."
  read -r -p "Press Return to close this window. "
fi
exit "$result"
