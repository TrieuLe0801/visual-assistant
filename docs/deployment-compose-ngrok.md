# Local Docker Compose deployment with ngrok

Date: 2026-11-08
Target: one Docker Desktop host, with an optional ngrok container for public HTTPS.

## Prepare

1. Start Docker Desktop. Put `NGROK_AUTHTOKEN` and, when needed, `NGROK_URL`
   in ignored `.env`. Compose passes them only to the optional ngrok container.
   The backend and frontend containers do not receive ngrok credentials.
2. Run `python3 scripts/init-deployment-secrets.py`. The script creates
   `.secrets/session_secret` and `.secrets/ngrok-basic-auth` with mode `0600`;
   it never replaces existing files. Both paths are Git and Docker ignored.
3. Set provider variables in ignored `.env` if image creation is needed.
   `OPENAI_API_KEY` is currently absent in the local environment; the web UI
   and account flows can start, but image operations cannot succeed without a
   working provider. Do not add credentials to `compose.yaml` or source files.
4. For a self-hosted provider running on the Mac, use a base URL reachable from
   the container, such as `http://host.docker.internal:8001/v1` on Docker
   Desktop, rather than `127.0.0.1` inside the container.

## Build and start

```bash
docker compose config --quiet
docker compose build app frontend
docker compose up -d --wait
docker compose ps
curl -fsS http://127.0.0.1:8000/api/health
```

The multi-stage Dockerfile builds the React bundle with Node 24, serves it
from Nginx, and syncs locked Python runtime dependencies with uv on Python
3.10. Compose runs a one-shot `database` service to initialize SQLite, one
FastAPI backend and one Nginx frontend. The frontend binds port 8000 only to
localhost and proxies `/api/` to the backend. SQLite and image files share the
named `visual_assistant_image_data` volume at `/data`. The app reads
`SESSION_SECRET_FILE=/run/secrets/session_secret` from a Compose secret. Cookies
are marked Secure for the ngrok HTTPS endpoint. Compose waits for backend and
frontend health checks; the database initializer exits with code 0.

## Publish

After placing an available ngrok token and optional URL in ignored `.env`,
start the `publish` profile:

```bash
docker compose --profile publish up -d --wait ngrok
docker compose --profile publish ps
docker compose --profile publish logs --tail=30 ngrok
```

The ngrok container forwards to `frontend:80` on the private Compose network.
It reads the Basic Auth credential from the `ngrok_basic_auth` Compose secret.
Use the HTTPS URL in the ngrok logs. Username is `studio`; read the password
from `.secrets/ngrok-basic-auth` on the deployment machine. Public visitors
must pass Basic Auth before reaching the app's own login page. Stop the tunnel
with `docker compose --profile publish stop ngrok`.

The tunnel URL depends on the ngrok account/domain. If its default domain is
already in use, use an available `NGROK_URL` or stop the existing endpoint under
that account. Do not enable endpoint pooling for this app.

## Backup and restore

Stop the ngrok service, if running, then stop the app before each backup so
SQLite and image files form one consistent snapshot. The frontend may continue
serving static files during this maintenance window. The default volume name
is shown below. If `IMAGE_DATA_VOLUME` was changed, use that name in both
`docker run` commands.

```bash
mkdir -p backups
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

- SQLite is embedded in the backend process. The `database` container only
  initializes its schema; it is not a long-running database server. One app
  host and one writable SQLite/image volume remain supported. Do not scale
  the app service to multiple containers.
- Keep `.secrets/` and backup archives out of Git and image builds. Rotate
  Basic Auth and session secret if their files are exposed. Changing the
  session secret signs out all users.
- Before rebuilding an existing deployment, retain the prior app image tag and
  a data backup. Recreate the container from the prior image tag for code
  rollback. SQLite schema changes may need a matching data restore.
- Live OpenAI, self-hosted and LangSmith delivery checks require credentials
  and active endpoints; a healthy container does not prove those calls work.
