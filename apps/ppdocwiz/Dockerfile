# PP Doc Wiz — standalone app (frontend + backend gateway) with the pp-document-suite engine embedded.
# BUILD CONTEXT = repo root (so it can COPY both pp-document-suite/ and ppdocwiz/):
#   docker build -f ppdocwiz/Dockerfile -t ppdocwiz:1.0 .
FROM python:3.11-slim

# LibreOffice + Calibri-compatible fonts for DOCX->PDF; poppler for rasterisation.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer fonts-crosextra-carlito fonts-liberation poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Requirements BEFORE the source trees: the pip layer then caches across source
# edits instead of being rebuilt on every change. Same ordering as
# apps/wwf-docengine/Dockerfile.
COPY ppdocwiz/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY pp-document-suite /opt/pp-document-suite
COPY ppdocwiz /app

ENV PP_SUITE_DIR=/opt/pp-document-suite \
    PP_OUT_DIR=/data
RUN mkdir -p /data
EXPOSE 8770

WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8770"]
