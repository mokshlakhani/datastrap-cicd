#!/usr/bin/env bash
# Deploys one container and rolls back if the new version is not healthy.
# Usage: ci/deploy.sh <container-name> <port> <new-image>
#   example: ci/deploy.sh datastrap-prod 8080 datastrap:42-ab12cd3
set -u                                   # stop on typos in variable names

NAME="$1"                                # e.g. datastrap-prod
PORT="$2"                                # port used inside AND outside the container (they must match)
NEW_IMAGE="$3"                           # image we want to run now
NETWORK="datastrap-ci"                   # same Docker network as Jenkins, so the smoke test can reach us

# Start a container from an image, using the settings every DataStrap container needs.
start() {
  docker run -d --name "$NAME" --restart unless-stopped \
    --network "$NETWORK" -e PORT="$PORT" -p "$PORT:$PORT" "$1" > /dev/null
}

# Wait up to 60 seconds for Docker's HEALTHCHECK to say "healthy".
wait_healthy() {
  for _ in $(seq 1 30); do
    status="$(docker inspect -f '{{.State.Health.Status}}' "$NAME" 2>/dev/null || echo missing)"
    [ "$status" = "healthy" ] && return 0
    sleep 2
  done
  return 1
}

# 1. Remember which image is running now (empty if this is the first deploy).
PREVIOUS_IMAGE="$(docker inspect -f '{{.Config.Image}}' "$NAME" 2>/dev/null || true)"
echo "Previous image: ${PREVIOUS_IMAGE:-none}"

# 2. Stop and remove the old container (if any), then start the new one.
docker rm -f "$NAME" > /dev/null 2>&1 || true
start "$NEW_IMAGE"

# 3. Healthy? Then we are done.
if wait_healthy; then
  echo "DEPLOY OK: $NAME is running $NEW_IMAGE on port $PORT"
  exit 0
fi

# 4. Not healthy: show why, remove it, and put the previous version back.
echo "NEW VERSION IS UNHEALTHY - last log lines:"
docker logs --tail 20 "$NAME" || true
docker rm -f "$NAME" > /dev/null 2>&1 || true
if [ -n "$PREVIOUS_IMAGE" ]; then
  echo "ROLLING BACK to $PREVIOUS_IMAGE"
  start "$PREVIOUS_IMAGE"
  wait_healthy && echo "Rollback finished: $PREVIOUS_IMAGE is healthy again" || echo "Rollback container is not healthy either!"
else
  echo "No previous version to roll back to."
fi
exit 1                                   # always fail the pipeline, so nobody thinks the deploy worked
