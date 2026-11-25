#!/bin/sh
# Run from the deployment checkout. Never print environment files or secrets.
set -eu

branch=$1
override=$2
log_group=$3

test -s core/.env || { echo 'Missing or empty core/.env'; exit 1; }
test -s docker.env || { echo 'Missing or empty docker.env'; exit 1; }
test -s jwt-paths.env || { echo 'Missing or empty jwt-paths.env'; exit 1; }
if [ "$branch" = main ]; then
  test -s docker.production.env || { echo 'Missing or empty docker.production.env'; exit 1; }
fi
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo 'Tracked local changes detected; deployment stopped.'
  exit 1
fi

git fetch origin "$branch"
if ! git diff --quiet HEAD "origin/$branch" -- docker.env; then
  echo 'Tracked docker.env would change; review it before deployment.'
  exit 1
fi
git reset --hard "origin/$branch"

# Use the same Compose project and files for preflight and deployment.
compose() {
  sudo env BILLY_AWS_REGION=us-east-1 BILLY_LOG_GROUP="$log_group" docker compose \
    --env-file docker.env --env-file jwt-paths.env -f docker-compose.yml -f "$override" "$@"
}

compose config --quiet
compose build web
# FileAwareEnv reads the mounted files here; settings validates the key pair.
compose run --rm --no-deps -T --entrypoint python web manage.py check
compose run --rm --no-deps -T --entrypoint python web manage.py shell -c \
  'from scripts.check_auth_preflight import check; check()'
# Never apply migrations implicitly: require the operator to review and apply
# pending migrations with a backup before any running service is recreated.
compose run --rm --no-deps -T --entrypoint python web manage.py migrate --check || {
  echo 'Database check failed or migrations are pending; review before deployment.'
  exit 1
}
compose up --build -d
