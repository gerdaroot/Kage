#!/bin/bash
# Kage 🖤 — Docker install: clones the repo, pulls the image and starts first-time login
set -e

if ! command -v docker >/dev/null 2>&1; then
    printf "\033[0;34mInstalling Docker...\033[0m\n"
    curl -fsSL https://get.docker.com | sudo sh
fi

# right after installing, the user isn't in the docker group yet
DOCKER="docker"
docker info >/dev/null 2>&1 || DOCKER="sudo docker"

[ -d Kage ] || git clone https://github.com/gerdaroot/Kage
cd Kage

$DOCKER compose pull || $DOCKER compose build
# two processes on one session file make Telegram revoke it (AUTH_KEY_DUPLICATED)
$DOCKER compose down

if ! $DOCKER compose run --rm --no-deps --entrypoint sh kage -c 'ls /data/sessions/kage-*.session' >/dev/null 2>&1; then
    printf "\033[0;35m🖤 Starting Kage — log in with the QR code or your phone number below\033[0m\n"
    printf "\033[0;35m   Once Kage reports it started, press Ctrl+C to move it to the background\033[0m\n"
    # Ctrl+C must stop only the first-start container, not this script (it still has to run `up -d`)
    trap : INT
    # under `curl | bash` stdin is the script itself, so the login prompts must read the terminal
    $DOCKER compose run --rm kage </dev/tty || true
    trap - INT
fi

$DOCKER compose up -d
printf "\033[0;32m🖤 Kage is running in the background: %s compose logs -f\033[0m\n" "$DOCKER"
