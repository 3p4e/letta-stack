# God's Eye View on KVM4
Upstream: https://github.com/bilawalsidhu/gods-eye-view (Node 24 Vite app, Dockerfile + compose.yaml, port 4173, MIT-style licence in repo).
Deploy: copy `docker-compose.yml` and `deploy.sh` to KVM4 (kvm4-runner `/file/write`), run `bash deploy.sh`.
URL: `https://gev.srv1231216.hstgr.cloud` (override with `GEV_HOST`), Traefik basic auth user `gev`.
Keys: add to `/opt/stacks/gods-eye-view/src/.env` (see upstream `.env.example`), then `docker compose up -d --force-recreate`.
No key is needed for the globe and most keyless layers (OpenSky anon, GTFS-RT, USGS, etc.).
