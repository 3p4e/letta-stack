# pp-render — the one document renderer (Head of QC, 10.10.2026): Gotenberg (LibreOffice) + the house fonts.
# Chosen over OnlyOffice by a side-by-side test against Word-made PDFs with the real fonts installed
# (label sheet, SOP-017, QCSOP_018 A01, WHSOP_003). LibreOffice matched Word; OnlyOffice did not.
#
# BUILD CONTEXT = /opt/fonts/pp on KVM4 (never this repository: the Microsoft fonts are licensed, not ours to publish):
#   /opt/fonts/pp/free       ← get_fonts.py (Microsoft core fonts, Google families incl. the CoQ/iCoA faces, Carlito)
#   /opt/fonts/pp/licensed   ← from a licensed Windows/Office PC: Calibri, Arial Narrow, Cambria Math, Segoe UI (+Symbol),
#                               MS Gothic, Tahoma, Arial Rounded MT Bold
#   docker build -t pp-render:8.37.0-fonts.1 -f server/render/Dockerfile /opt/fonts/pp
FROM gotenberg/gotenberg:8.37.0
USER root
COPY --chmod=644 free/ /usr/local/share/fonts/pp/free/
COPY --chmod=644 licensed/ /usr/local/share/fonts/pp/licensed/
RUN find /usr/local/share/fonts/pp -type d -exec chmod 755 {} + && fc-cache -f >/dev/null
USER gotenberg
