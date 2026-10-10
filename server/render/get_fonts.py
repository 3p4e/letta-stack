"""Fetch the free house fonts as installable static TTFs into /opt/fonts/pp/free (pp-render build context).

    docker run --rm -v "$PWD":/w -v /opt/fonts/pp:/o python:3.12-slim sh -c \
      "apt-get update -qq && apt-get install -y -qq cabextract && pip install -q fonttools==4.62.1 \
       && python /w/get_fonts.py /o/free"

- Microsoft core fonts (redistributable EULA): from the corefonts SourceForge project, unpacked with cabextract.
- Google families: from github.com/google/fonts; static files as published, variable ones instanced
  to the weights the house documents use (a variable font does not embed reliably in a PDF).
"""
import io, os, re, subprocess, sys, urllib.request
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
RAW = "https://raw.githubusercontent.com/google/fonts/main/"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pp-fonts/1.0"}), timeout=60).read()

# ---- Microsoft core fonts ----
core = os.path.join(OUT, "ms-core"); os.makedirs(core, exist_ok=True)
for exe in ["arial32", "arialb32", "times32", "courie32", "verdan32", "trebuc32", "georgi32", "impact32", "webdin32", "andale32", "comic32"]:
    p = os.path.join(core, exe + ".exe")
    open(p, "wb").write(get(f"https://downloads.sourceforge.net/corefonts/{exe}.exe"))
    subprocess.run(["cabextract", "-q", "-L", "-F", "*.ttf", "-d", core, p], check=True)
    os.remove(p)

# ---- Google families: (repo dir, family name, upright weights, italic weights) ----
FAM = [
    ("ofl/montserrat", "Montserrat", [300, 400, 500, 600, 700, 800, 900], [300, 400, 500, 600, 700, 800]),
    ("ofl/robotomono", "Roboto Mono", [400, 500, 600, 700], [400, 500, 600, 700]),
    ("ofl/orbitron", "Orbitron", [400, 500, 600, 700, 800, 900], []),
    ("ofl/robotocondensed", "Roboto Condensed", [400, 500, 600, 700], [400, 500, 600, 700]),
    ("ofl/carlito", "Carlito", None, None),
    # WWF / GrowFlow web faces
    ("ofl/saira", "Saira", [400, 500, 600, 700, 800], []),
    ("ofl/sairacondensed", "Saira Condensed", None, None),
    ("ofl/titilliumweb", "Titillium Web", None, None),
    ("ofl/poppins", "Poppins", None, None),
    ("ofl/geistmono", "Geist Mono", [400, 500, 600], []),
    ("ofl/ibmplexsans", "IBM Plex Sans", [400, 500, 600, 700], [400]),
    ("ofl/ibmplexmono", "IBM Plex Mono", None, None),
    ("ofl/ibmplexserif", "IBM Plex Serif", None, None),
    ("ofl/inter", "Inter", [300, 400, 500, 600, 700, 800], [400]),
    ("ofl/jetbrainsmono", "JetBrains Mono", [400, 500, 600], [400]),
    ("ofl/archivo", "Archivo", [500, 600, 700], []),
    ("ofl/publicsans", "Public Sans", [400, 500, 600], [400]),
]
WNAME = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold",
         700: "Bold", 800: "ExtraBold", 900: "Black"}

def rename(f, family, w, italic):
    style = WNAME[w] + (" Italic" if italic else "")
    if style == "Regular Italic": style = "Italic"
    # RIBBI: Regular/Bold(/Italic) keep the family name; other weights get "Family Weight"
    ribbi = w in (400, 700)
    fam1 = family if ribbi else f"{family} {WNAME[w]}"
    sub1 = ("Bold " if w == 700 else "") + ("Italic" if italic else "")
    sub1 = sub1.strip() or "Regular"
    full = f"{family} {style}".replace(" Regular", "") if style != "Regular" else family
    ps = (family.replace(" ", "") + "-" + style.replace(" ", ""))
    n = f["name"]
    for nid, val in ((1, fam1), (2, sub1), (4, full), (6, ps), (16, family), (17, style)):
        n.setName(val, nid, 3, 1, 0x409)
    f["OS/2"].usWeightClass = w
    sel = f["OS/2"].fsSelection & ~0b1100001  # clear ITALIC, BOLD, REGULAR
    sel |= (1 if italic else 0) | (0b100000 if w == 700 else 0) | (0b1000000 if (w == 400 and not italic) else 0)
    f["OS/2"].fsSelection = sel
    f["head"].macStyle = (1 if w == 700 else 0) | (2 if italic else 0)

for d, family, ups, its in FAM:
    meta = get(RAW + d + "/METADATA.pb").decode()
    files = re.findall(r'filename:\s*"([^"]+)"', meta)
    dest = os.path.join(OUT, "google", family.replace(" ", ""))
    os.makedirs(dest, exist_ok=True)
    for fn in files:
        data = get(RAW + d + "/" + fn.replace("[", "%5B").replace("]", "%5D"))
        if "[" not in fn:                      # static file: keep as published
            open(os.path.join(dest, fn), "wb").write(data); continue
        italic = "Italic" in fn
        for w in (its if italic else ups) or []:
            f = TTFont(io.BytesIO(data))
            axes = {a.axisTag: a for a in f["fvar"].axes}
            loc = {"wght": max(axes["wght"].minValue, min(axes["wght"].maxValue, w))}
            for tag, a in axes.items():
                if tag != "wght": loc[tag] = a.defaultValue
            inst = instantiateVariableFont(f, loc)
            rename(inst, family, w, italic)
            inst.save(os.path.join(dest, f"{family.replace(' ', '')}-{WNAME[w]}{'Italic' if italic else ''}.ttf"))
    print(f"{family}: {len(os.listdir(dest))} files")
print("ms-core:", len([x for x in os.listdir(core) if x.endswith('.ttf')]), "files")
