#!/bin/bash
# Kage 🖤 — Docker install: clones the repo, pulls the image and starts first-time login
set -e

if ! command -v docker >/dev/null 2>&1; then
    printf "\033[0;34mInstalling Docker...\033[0m\n"
    curl -fsSL https://get.docker.com | sudo sh
fi

[ -d Kage ] || git clone https://github.com/gerdaroot/Kage
cd Kage

printf "\033[0;35m🖤 Starting Kage — log in with the QR code or your phone number below\033[0m\n"
docker compose pull || docker compose build
docker compose run --rm kage
docker compose up -d
printf "\033[0;32m🖤 Kage is running in the background: docker compose logs -f\033[0m\n"
