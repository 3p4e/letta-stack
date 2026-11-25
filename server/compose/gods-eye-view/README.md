# God's Eye View on KVM4
Upstream: https://github.com/bilawalsidhu/gods-eye-view (Node 24 Vite app, port 4173), pinned by commit in the compose.
Deployed via the Hostinger VPS Docker API as project `gods-eye-view` (host-network Traefik, `letsencrypt`).
URL `https://gev.srv1231216.hstgr.cloud`, basic-auth user `gev` (password held by the Head of QC, not in the repo).
Keys: set `OPENAI_API_KEY`, `AISSTREAM_API_KEY` (others per upstream `.env.example`) in the project environment and redeploy.
