# pp-render — the one document renderer

Gotenberg 8.37.0 (LibreOffice) with the Purely Plant house fonts built in. Every client renders through it via
`pp-document-suite/scripts/pp_render.py` (`GOTENBERG_URL`). Why LibreOffice and why the fonts matter, how to add a
font, and the deployment record: `server/runbooks/docengine_knowledge_and_render.md` §2 and "Deployed — 10.10.2026".

| file | what |
|---|---|
| `Dockerfile` | `FROM gotenberg/gotenberg:8.37.0` + `/opt/fonts/pp/{free,licensed}` + `fc-cache` (build context `/opt/fonts/pp`) |
| `compose.yaml` | KVM4 `/opt/stacks/pp-render`: container `gotenberg` on `ai-net`, Traefik route with basic auth |
| `get_fonts.py` | fetches the free fonts into `/opt/fonts/pp/free` (static TTFs; variable fonts instanced) |

The licensed Microsoft fonts are never committed — they stay in `/opt/fonts/pp/licensed` on the server.
