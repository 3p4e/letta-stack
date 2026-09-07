# Видео презентации · Video presentations
## RAGFlow — платформа за интелигентна обработка на QC документи

Два филма за истата платформа, наменети за различна публика и снимени со
две различни машини за рендерирање. Обата се со професионална нарација на
**македонски јазик** и се самостојни `.mp4` датотеки — не бараат интернет,
приклучок или сметка за да се пуштат.

Two films about the same platform, aimed at different audiences and produced
with two different rendering engines. Both carry professional **Macedonian**
narration and ship as self-contained `.mp4` files — no network, plugin or
account needed to play them.

---

## Филм 1 — „Извршен брифинг“ | Executive Briefing

`film1_izvrsen_brifing.mp4` · 1920×1080 · 24 fps · 2 мин 22 сек

Темен, кинематски брифинг воден од податоци. Наменет за раководство и за
отворање на состанок: што беше проблемот, што е изградено, што покажуваат
бројките, и зошто платформата е бранлива пред инспекција.

Dark, data-led cinematic briefing. Built for management and for opening a
meeting: what the problem was, what was built, what the numbers say, and why
the platform is defensible under inspection.

| Сцена | Содржина |
|---|---|
| 01 | Насловна — 480 документи, 11.088 сегменти, 1.038 параметри, €0 лиценци |
| 02 | Три отворени ризика пред системот |
| 03 | Архитектура — пет компоненти на сопствен сервер KVM4 |
| 04 | Патека на обработка — пет чекори |
| 05 | OCR каскада — три модели, Tesseract никогаш |
| 06 | Интегритет — заменува, не додава |
| 07 | Бројки — 389 / 385 / 1.038 |
| 08 | Заклучок — „Ова не е прототип.“ |

---

## Филм 2 — „Патот на еден сертификат“ | The Journey of One Certificate

`film2_pat_na_sertifikat.mp4` · 1920×1080 · 24 fps · 1 мин 32 сек

Светол технички цртеж на хартија, што се исцртува пред гледачот. Наместо
бројки, филмот следи **еден единствен сертификат** низ седумте чекори на
системот. Наменет за колеги што не се од ИТ — објаснува како работи
платформата преку приказна, не преку статистика.

A light technical drawing on paper that draws itself as you watch. Instead of
figures, it follows **one single certificate** through the system's seven
steps. Aimed at non-IT colleagues — it explains the platform through a story
rather than statistics.

| Лист | Содржина |
|---|---|
| 01 | Појдовна точка — хартија, печат, броеви |
| 02 | Прием и отпечаток — SHA-256 при влез |
| 03 | Читање на документот — скенирање наспроти разбирање |
| 04 | Идентитет на содржината — три податоци, еден клуч |
| 05 | Векторизација — значењето станува мерливо |
| 06 | Прашање и одговор — со извор за секој број |
| 07 | Преиздавање — заменува, не додава |
| 08 | Целосна следливост |

---

## Како се направени | How they were made

Двата филма делат еден извор на нарација и две сосема различни машини за
слика. Ниту еден кадар не е снимен — сè е пресметано.

| | Филм 1 | Филм 2 |
|---|---|---|
| Машина за слика | Chromium преку Playwright | Python · Pillow + NumPy |
| Визуелен јазик | темна кинематска графика | технички цртеж на хартија |
| Букви | Oswald · IBM Plex Sans · JetBrains Mono | PT Sans · IBM Plex Mono |
| Глас | ElevenLabs `eleven_v3`, машки | ElevenLabs `eleven_v3`, женски |
| Кадри | 3.412 | 2.207 |

**Заедничко:** нарацијата е синтетизирана прва, должината на секој сегмент е
измерена, и тие должини ја диктираат временската рамка на сликата
(`film*_timeline.json`). Затоа сликата и гласот се совпаѓаат точно — секој
елемент се појавува на својот збор, а не на приближна проценка.

Narration is synthesised **first**; each segment's real duration is measured and
those durations drive the picture timeline (`film*_timeline.json`). That is why
image and voice line up exactly — every element appears on its own word rather
than on a guess.

Обете машини рендерираат детерминистички: `render(t)` е чиста функција од
времето, без анимации во CSS и без случајност. Секој кадар се пренесува
директно во `ffmpeg` како MJPEG, без запис на диск.

Both engines render deterministically: `render(t)` is a pure function of time —
no CSS animation, no randomness. Frames are piped straight into `ffmpeg` as
MJPEG, never written to disk.

### Повторно градење | Rebuilding

```bash
cd src
export ELEVENLABS_API_KEY=...            # само за повторна нарација
python3 narration.py                     # проверка на должина и буџет
python3 tts.py both                      # глас + timeline.json + master audio

# Филм 1 — Chromium
NODE_PATH=/opt/node22/lib/node_modules \
FFMPEG_BIN=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())") \
node capture.js render

# Филм 2 — Pillow
python3 film2.py render
```

Со `stills` наместо `render` двете машини вадат поединечни кадри за проверка
на композицијата пред целосно рендерирање.

Passing `stills` instead of `render` makes either engine emit single frames for
composition checks before committing to a full render.

### Зависности | Dependencies

- `playwright` (Chromium) — Филм 1
- `Pillow`, `numpy` — Филм 2
- `imageio-ffmpeg` — H.264 / AAC кодирање за обата
- Букви со целосна македонска поддршка (Oswald, PT Sans, IBM Plex, JetBrains
  Mono) се преземаат во `src/fonts/`; **Barlow Condensed не е употреблив —
  нема кирилица.**

---

## Забелешка за податоците | Note on the data

Сите бројки во обата филма се земени од живата состојба на RAGFlow на
KVM4 (август 2026): 389 документи во `eCOA_INGEST` од кои 385 целосно
пребарливи, 81 во `eCOA_INGEST_SUMMA`, 10 во `STABILITY_PROGRAMME`,
и 1.038 потврдени параметри низ 49 серии. Ниту една бројка не е заокружена
нагоре заради ефект.

Every figure in both films comes from the live RAGFlow state on KVM4
(August 2026). No number is rounded up for effect.
