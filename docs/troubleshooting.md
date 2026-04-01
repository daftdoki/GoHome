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
