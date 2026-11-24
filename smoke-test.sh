#!/usr/bin/env bash
# Hosted acceptance uses private credentials; never pass passwords in arguments.
set -euo pipefail
source_dir=${1:?Usage: ./smoke-test.sh /path/to/GC-AI --image diagram.png --output new-private-directory}
shift
exec python3 "$source_dir/tools/verify_deployment.py" "$@"
