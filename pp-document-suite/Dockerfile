# Purely Plant Document Suite — dedicated build-service container.
# Build context = the pp-document-suite/ directory.  Produces a REST service (integrations/service.py)
# on :8600 that generates house-style .docx (and PDF via LibreOffice). Join it to the Letta stack's
# network so Letta agents reach it at http://pp-document-suite:8600.
FROM python:3.11-slim

# LibreOffice for DOCX->PDF; Carlito/Liberation are metric-compatible substitutes for Calibri/Arial
# so rendered PDFs match Word. poppler-utils gives pdftoppm for page rasterisation/eyeballing.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer fonts-crosextra-carlito fonts-liberation poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/pp-document-suite
COPY . /opt/pp-document-suite

# Core deps always; latex2mathml enables native Word equations (falls back to text without it).
RUN pip install --no-cache-dir python-docx lxml fastapi "uvicorn[standard]" latex2mathml

ENV PP_SUITE_DIR=/opt/pp-document-suite \
    PP_OUT_DIR=/data
RUN mkdir -p /data
EXPOSE 8600

WORKDIR /opt/pp-document-suite/integrations
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8600"]
