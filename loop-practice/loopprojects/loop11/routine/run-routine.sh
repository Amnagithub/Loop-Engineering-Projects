#!/usr/bin/env bash
# run-routine.sh — run a routine prompt ONCE as an unattended session and
# capture (a) its STATUS line and (b) its FULL TRANSCRIPT, so a Routine can
# be rehearsed locally before it is trusted with a real gate.
#
# A copy of loop9's harness, pointed at loop11/routine/results/runs so the
# two Routine prompts of Project 11 can be rehearsed the same way loop9
# rehearsed its routine (status is coarse; the transcript is truth).
#
# Usage (from the git repo root):
#   bash loop-practice/loopprojects/loop11/routine/run-routine.sh <prompt-file> <run-label>
# e.g.
#   bash loop-practice/loopprojects/loop11/routine/run-routine.sh \
#       loop-practice/loopprojects/loop11/routine/prompt-a.md 01-a-draft
#
# Routine B's prompt needs the human's approval token as an env var. Fire it
# only after `gate.py approve` (it then prints the token); pass it through:
#   APPROVAL_TOKEN=<token printed by approve> \
#   bash loop-practice/loopprojects/loop11/routine/run-routine.sh \
#       loop-practice/loopprojects/loop11/routine/prompt-b.md 02-b-act
set -u

PROMPT_FILE="${1:?usage: run-routine.sh <prompt-file> <run-label>}"
RUN_LABEL="${2:?usage: run-routine.sh <prompt-file> <run-label>}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 2

REL_PROMPT="${PROMPT_FILE#./}"
PROMPT_TEXT="$(cat "$REL_PROMPT")"
OUT_DIR="loop-practice/loopprojects/loop11/routine/results/runs/$RUN_LABEL"
RAW="$OUT_DIR/.raw-run.json"
mkdir -p "$OUT_DIR"

# A routine runs with no permission prompts and a bounded tool set.
ALLOWED="Read,Write,Glob,Grep,Bash(git*),Bash(cat*),Bash(python*)"

export CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=200000
claude -p "$PROMPT_TEXT" \
  --output-format json \
  --allowedTools "$ALLOWED" \
  > "$RAW" 2>"$OUT_DIR/stderr.log"
CLAUDE_EXIT=$?

node -e '
const fs=require("fs");
const raw=fs.readFileSync(process.argv[1],"utf8").trim();
if(!raw){process.exit(1)}
const o=JSON.parse(raw);
fs.writeFileSync(process.argv[2], JSON.stringify({
  status_line: {
    subtype: o.subtype,
    is_error: o.is_error,
    terminal_reason: o.terminal_reason,
    stop_reason: o.stop_reason,
    result: o.result,
    total_cost_usd: o.total_cost_usd,
  },
  session_id: o.session_id,
}, null, 2));
' "$RAW" "$OUT_DIR/STATUS.json"

SESSION_ID="$(node -e 'try{console.log(JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).session_id||"")}catch(e){}' "$RAW")"
if [ -n "$SESSION_ID" ]; then
  TRANSCRIPT="$(find "$HOME/.claude/projects" -name "$SESSION_ID.jsonl" 2>/dev/null | head -1)"
  if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    cp "$TRANSCRIPT" "$OUT_DIR/transcript.jsonl"
    printf 'run-label: %s\nprompt-file: %s\nexit-code: %s\nsession-id: %s\n' \
      "$RUN_LABEL" "$REL_PROMPT" "$CLAUDE_EXIT" "$SESSION_ID" > "$OUT_DIR/ARTIFACTS.txt"
  fi
fi
rm -f "$RAW"

echo "==== $RUN_LABEL done (claude exit $CLAUDE_EXIT) ===="
echo "status:  $(node -e 'const o=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"));console.log("subtype="+o.status_line.subtype+" is_error="+o.status_line.is_error+" reason="+o.status_line.terminal_reason)' "$OUT_DIR/STATUS.json" 2>/dev/null)"
echo "artifacts in: $OUT_DIR"
