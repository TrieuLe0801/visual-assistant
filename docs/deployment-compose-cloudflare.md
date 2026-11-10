# Local Docker Compose deployment with Cloudflare Tunnel

Date: 2026-11-09
Target: one Docker Desktop host, with an optional Cloudflare Quick Tunnel.

## Prepare

1. Start Docker Desktop. Quick Tunnel needs no Cloudflare token or domain.
2. Run `python3 scripts/init-deployment-secrets.py`. It creates
   `.secrets/session_secret` with mode `0600` and never replaces an existing
   file. The path is Git and Docker ignored.
3. Set provider variables in ignored `.env` if image creation is needed.
   Without a working prompt model and image provider, account flows can start
   but image operations cannot succeed. The prompt interpreter uses
   `PROMPT_MODEL`, `PROMPT_API_BASE_URL` and `PROMPT_API_KEY`; if the latter is
   blank and its endpoint matches `OPENAI_BASE_URL`, it falls back to
   `OPENAI_API_KEY`. A separate endpoint uses its own optional key.
4. For a self-hosted provider running on the Mac, use a base URL reachable from
   the container, such as `http://host.docker.internal:8001/v1` on Docker
   Desktop, rather than `127.0.0.1` inside the container.

Compose reads provider variables when it creates the backend container. After
changing `.env`, apply the new values with
`docker compose up -d --no-deps --force-recreate app`. A container restart
alone does not reload changed Compose environment values.

## Build and start

```bash
docker compose config --quiet
docker compose build app frontend
docker compose up -d --wait
docker compose ps
curl -fsS http://127.0.0.1:8088/api/health
```

Compose runs a one-shot SQLite initializer, one FastAPI backend and one Nginx
frontend. The frontend binds host port 8088 only to localhost and proxies
`/api/` to FastAPI. Set `FRONTEND_PORT` in ignored `.env` if 8088 is occupied.
SQLite and image files share the named `visual_assistant_image_data` volume at
`/data`. The app reads its session secret from a Compose secret. Cookies are
marked Secure because public traffic uses HTTPS.

## Publish with Quick Tunnel

Start the `publish` profile after the frontend is healthy:

```bash
docker compose --profile publish up -d cloudflared
docker compose --profile publish ps
docker compose --profile publish logs --tail=50 cloudflared
```

The `cloudflared` container forwards to `frontend:80` over the private Compose
network. Copy the temporary `https://….trycloudflare.com` URL from its logs.
Quick Tunnel URLs change when the tunnel process restarts. Stop publishing with
`docker compose --profile publish stop cloudflared`.

Quick Tunnel has no Cloudflare Access policy by default. Anyone with the URL can
reach the app's registration and login screens. The app scopes image data by
owner and applies persistent safety rate limits: 12 registrations/hour globally,
3/hour per email, 300 logins/15 minutes globally, 20/15 minutes per email,
120 image operations/day globally and 24/day per user. These limits can deny
legitimate traffic when shared capacity is exhausted; they are not a billing
quota. Use Quick Tunnel only for trusted testing. To require email verification
for a host-run tunnel, start
`cloudflared tunnel --url http://127.0.0.1:8088 --allowed-mail you@example.com`
instead of the Compose `cloudflared` service. Repeat `--allowed-mail` for each
allowed address.

For stable custom domains, create a remotely-managed named tunnel in Cloudflare,
add one published application route per hostname, and add a Cloudflare Access
policy before sharing the URLs. Store its tunnel token as a Compose secret; do
not put it in source or expose it to the app. This repository currently
configures Quick Tunnel only.

## Backup and restore

Stop the Cloudflare tunnel, then stop the app before each backup so SQLite and
image files form one consistent snapshot. The frontend may continue serving
static files during this maintenance window. The default volume name is shown
below. If `IMAGE_DATA_VOLUME` was changed, use that name in both `docker run`
commands.

```bash
mkdir -p backups
docker compose --profile publish stop cloudflared
docker compose stop app
docker run --rm --user 0 \
  --mount type=volume,src=visual_assistant_image_data,dst=/data,readonly \
  --mount type=bind,src="$PWD/backups",dst=/backups \
  image-studio:local tar -czf /backups/image-studio-backup.tgz -C /data .
docker compose start app
```

Keep backup archives outside the deployment host as required by the operating
policy. To test or restore, extract into a **new** volume, then switch Compose
to that volume. This preserves the previous volume for rollback.

```bash
docker volume create visual_assistant_image_data_restored
docker run --rm --user 0 \
  --mount type=volume,src=visual_assistant_image_data_restored,dst=/data \
  --mount type=bind,src="$PWD/backups",dst=/backups,readonly \
  image-studio:local sh -c \
  'tar -xzf /backups/image-studio-backup.tgz -C /data && chown -R 10001:10001 /data'
IMAGE_DATA_VOLUME=visual_assistant_image_data_restored docker compose up -d --no-build --wait
```

Check `/api/health`, then verify a known account and image file after a real
restore. Roll back to the prior volume with `docker compose up -d --no-build
--force-recreate` using its prior `IMAGE_DATA_VOLUME`. Do not delete the prior
volume until the restore is verified.

## Limits and recovery

- The Docker host and `cloudflared` container must stay online for the URL to
  work. Quick Tunnel has no uptime guarantee, allows up to 200 in-flight
  requests and does not support Server-Sent Events.
- SQLite is embedded in the backend process. The `database` container only
  initializes its schema; it is not a long-running database server. One app
  host and one writable SQLite/image volume remain supported. Do not scale
  the app service to multiple containers.
- Keep `.secrets/` and backup archives out of Git and image builds. Changing the
  session secret signs out all users.
- The backend image uses Python 3.11 and Pillow 13.0.0. Python 3.10 remains
  supported for development but resolves Pillow 12.3.0, which has known
  security advisories; do not serve untrusted images from a Python 3.10 runtime.
- Before rebuilding an existing deployment, retain the prior app image tag and
  a data backup. Recreate the container from the prior image tag for code
  rollback. SQLite schema changes may need a matching data restore.
- Live OpenAI, self-hosted and LangSmith delivery checks require credentials
  and active endpoints; a healthy container does not prove those calls work.
- A user can request 1–6 images per creation action. The browser sends separate
  requests, each with its own provider and prompt-model cost. Reloading the
  page stops later requests but leaves completed results in the library.
- Deleting an image removes its live file and hides it from the image API.
  SQLite retains a metadata tombstone for derived-image lineage. Older backup
  archives may still contain files deleted after the backup was made.

## References

- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
- [Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/get-started/)
- [Cloudflare Access for public applications](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/)
