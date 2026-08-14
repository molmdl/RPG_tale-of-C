#!/usr/bin/env bash
# tools/run_headless.sh -- reusable WSL->Windows headless PyMOL bridge wrapper.
# Usage: bash tools/run_headless.sh <script.py>
# MUST run with cwd = repo root (so os.getcwd()=workspace and `import c14` works
# -- see 03-RESEARCH.md Gotcha #2/#3/#4). The caller (execute-plan) runs with
# workdir=repo-root, so cwd is already correct when invoked the normal way.
#
# The process exit code is ALWAYS 0 through the bat (conda deactivate overwrites
# %ERRORLEVEL%; PyMOL's parsing.run_file swallows exceptions -- 03-RESEARCH.md
# Gotcha #1). The verdict comes from the script's SMOKE_RESULT: stdout sentinel,
# which this wrapper greps for ^SMOKE_RESULT: PASS. Exit code is used ONLY for
# infra-failure detection (timeout=124, segfault=139, conda-activation fail).

SCRIPT="$1"
if [ -z "$SCRIPT" ]; then
    echo "usage: bash tools/run_headless.sh <script.py>" >&2
    exit 2
fi

# Resolve the script to a Windows-readable absolute path (wslpath -w is more
# reliable than the wsl$-UNC form per 03-RESEARCH.md section 1).
WIN_SCRIPT=$(wslpath -w "$(pwd)/$SCRIPT")

# Capture all stdout+stderr to a temp file for inspection on failure.
OUT="/tmp/opencode/$(basename "$SCRIPT" .py).txt"
mkdir -p /tmp/opencode
timeout 150 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq $WIN_SCRIPT" > "$OUT" 2>&1
EXIT=$?
echo "headless output: $OUT (raw exit=$EXIT)"

if [ "$EXIT" -eq 124 ]; then
    echo "FAILED: timeout (150s)"
    cat "$OUT"
    exit 1
fi
if [ "$EXIT" -ne 0 ]; then
    echo "FAILED: infra error (exit=$EXIT; 0=launched, 124=timeout)"
    cat "$OUT"
    exit 1
fi

# Verdict via STDOUT sentinel (NOT $? -- the bat always returns 0).
# Robust check: PASS-presence (presence = pass; absence = fail). This is
# stricter than grepping for FAIL -- a crash before the sentinel prints would
# falsely "pass" a FAIL-grep form. Encode the PASS-presence check.
if grep -q "^SMOKE_RESULT: PASS" "$OUT"; then
    echo "PASSED"
    exit 0
else
    echo "FAILED (no ^SMOKE_RESULT: PASS sentinel)"
    cat "$OUT"
    exit 1
fi
