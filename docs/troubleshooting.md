# GoHome Troubleshooting

Operational troubleshooting for deploying and running GoHome.

---

## Tailscale: Hostname "go" is already taken

**Problem:** After moving to a new host or recreating the Docker stack
without preserving the `ts-state` volume, Tailscale treats the new
container as a different node and assigns a suffixed hostname like
`go-1`.

**Solution:**

1. Stop the current stack:
   `docker compose down`
2. Open the
   [Tailscale admin console](https://login.tailscale.com/admin/machines)
3. Find the stale `go` machine (usually shown as offline) and remove it
   via **...** > **Remove**
4. Delete the local Tailscale state so the container re-registers
   cleanly:
   `docker volume rm gohome_ts-state`
   (the volume name may differ — check with `docker volume ls`)
5. Restart the stack:
   `docker compose up -d`
6. Confirm the machine appears as **go** in the admin console

**Prevention:** Use a reusable auth key with a tag so that
re-registration is seamless when moving between hosts.

---

## Checking container health

**Problem:** The GoHome container is running but the site does not
respond, or a deploy fails waiting for the container to become healthy.

**Solution:**

The image has a healthcheck that requests `http://127.0.0.1:$GOHOME_PORT/`
every 30 seconds. It marks the container `unhealthy` after three
consecutive failures.

1. See the status in the `STATUS` column:
   `docker compose ps`
   (`healthy`, `unhealthy`, or `health: starting` during the first
   10 seconds)
2. See the recent check results and error output:
   `docker inspect --format '{{json .State.Health}}' <container>`
   (find the name with `docker compose ps`)
3. Read the app logs:
   `docker compose logs --tail 50 gohome`

**Notes:** The post-receive deploy hook runs
`docker compose up -d --wait --wait-timeout 60` and prints the last 50
log lines if the container is not healthy in time.
