#!/usr/bin/env bash
# Environment setup script for running the science briefing as a scheduled routine.
#
# Paste a filled-in copy into your cloud environment's setup script. It writes your
# user config and profile to ~/.science-newsletter/, where agents/science-briefer.md
# looks for them, so personal details never live in the routine prompt or in git.
#
# Replace <username> and the two heredoc bodies with the contents of your
# config/users/<username>.json and agents/users/<username>.md.
set -euo pipefail

USER_SLUG="<username>"
DEST="${SCIENCE_NEWSLETTER_HOME:-$HOME/.science-newsletter}"
mkdir -p "$DEST/config/users" "$DEST/agents/users"

cat > "$DEST/config/users/$USER_SLUG.json" <<'SCIENCE_NEWSLETTER_CONFIG'
{ "user": "<username>", "...": "paste config/users/<username>.json here" }
SCIENCE_NEWSLETTER_CONFIG

cat > "$DEST/agents/users/$USER_SLUG.md" <<'SCIENCE_NEWSLETTER_PROFILE'
# User Profile — paste agents/users/<username>.md here
SCIENCE_NEWSLETTER_PROFILE

python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$DEST/config/users/$USER_SLUG.json"
echo "science-newsletter: wrote config and profile for $USER_SLUG to $DEST"
