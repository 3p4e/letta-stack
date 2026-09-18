#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The option vocabulary of the internal certificate of analysis.

    python3 icoa_handoff/findings_options.py        # print the vocabulary and its counts

The Head of QC, 17.09.2026, on the internal certificates of analysis:

> "I want you to restructure the parts that describe the findings. Let's give you a
> suggestion maybe with a pre-given options for checking for various parameters … per
> parameter, so the user can check and include into the certificate. Same as in the
> foreign matter analysis, maybe use some variables that are connected or relevant to the
> findings or expected results from the foreign matter and also from macroscopy and
> microscopy. Regarding odour, regarding colours, give several options."

So the observation is a **menu**, not free prose: every finding the laboratory can record
for identification A, identification B and foreign matter is written down here once, and
the certificate prints the whole menu with a box against each option. What the analyst
observed is marked; what was not observed is visibly not marked. A menu is auditable
where a blank line is not — two analysts describing the same flower in their own words
produce two different records, and neither can be compared with the next batch.

## Why the certificates print the menu unticked

The desk holds **no observation-level record** for these three determinations. Every
source it has — the certificates of quality, the 09.09 cell resolution, both registers —
carries one word per determination, `Conforms`, and nothing beneath it. The redesign
therefore prints:

* the **verdict** the record actually carries, in the results table, as the certificate
  of quality prints it; and
* the **observation menu** unticked, as the completable bench record, to be marked and
  initialled by hand beside the signature that is likewise left for wet ink.

The desk does not invent a colour, an odour or a trichome density it was never told. The
convention is stated on the page itself, so a reader cannot mistake an unticked menu for
an absent analysis, and it is registered as an open item for the Head of QC.

## The vocabulary

Every option is a pair — English, then the Macedonian the certificate of quality uses for
the same idea. The macroscopic and microscopic terms are the monograph's: *Cannabis flos*
(Ph. Eur. 11.5, 07/2024:3028) for the appearance and Ph. Eur. 2.8.23 for the powdered-drug
microscopy, whose diagnostic structures for Cannabis are the cystolithic covering
trichomes, the glandular trichomes of the three forms, the calcium oxalate clusters and
the anomocytic stomata. The foreign-matter categories are those of Ph. Eur. 2.8.2 together
with the two the in-house specification adds — leaves over 1 cm and seeds, which QCSP-001
names explicitly.

Deviations are in the same menu as the expected findings, marked `dev=True`. A menu that
can only record a good result is not a record, it is a rubber stamp; the analyst must be
able to tick "musty" on this form, and the form must show that they did not.
"""
import io
import os
import sys


class Opt(object):
    """One checkable option: its English and Macedonian label, and whether it is a
    deviation from the expected finding (printed in the warning ink)."""

    __slots__ = ("en", "mk", "dev")

    def __init__(self, en, mk, dev=False):
        self.en, self.mk, self.dev = en, mk, dev


def O(en, mk):
    return Opt(en, mk, False)


def D(en, mk):
    """A deviation — an observation that puts the determination in doubt."""
    return Opt(en, mk, True)


# ---------------------------------------------------------------------------
# #1 · Identification A, Appearance · Macroscopic · Ph. Eur. monograph 3028
# ---------------------------------------------------------------------------
MACROSCOPY = [
    ("Form", "Форма", [
        O("Whole inflorescence", "Цело соцветие"),
        O("Trimmed inflorescence", "Тримувано соцветие"),
        O("Fragmented", "Фрагментирано"),
        O("Compressed", "Збиено"),
    ]),
    ("Colour", "Боја", [
        O("Light green", "Светлозелена"),
        O("Medium green", "Средно зелена"),
        O("Dark green", "Темнозелена"),
        O("Olive green", "Маслинеста"),
        O("Purple tinge", "Виолетов призвук"),
        D("Brown tinge", "Кафеав призвук"),
        D("Faded, bleached", "Избледена"),
    ]),
    ("Stigmas", "Жигови", [
        O("Orange-brown", "Портокалово-кафеави"),
        O("Red-brown", "Црвено-кафеави"),
        O("Amber", "Килибарни"),
        O("Pale", "Бледи"),
    ]),
    ("Trichome coverage", "Покриеност со трихоми", [
        D("Sparse", "Ретка"),
        O("Moderate", "Умерена"),
        O("Dense", "Густа"),
        O("Very dense", "Многу густа"),
    ]),
    ("Trichome heads", "Главички на трихоми", [
        O("Clear", "Бистри"),
        O("Cloudy", "Матни"),
        O("Cloudy with amber", "Матни со килибарни"),
        O("Predominantly amber", "Претежно килибарни"),
    ]),
    ("Odour", "Мирис", [
        O("Characteristic, aromatic", "Карактеристичен, ароматичен"),
        O("Terpenic, citrus", "Терпенски, цитрусен"),
        O("Earthy, woody", "Земјен, дрвенест"),
        O("Sweet, fruity", "Сладок, овошен"),
        O("Spicy, peppery", "Зачински, пиперлив"),
        O("Pungent", "Остар"),
        D("Musty, mouldy", "Мувлосан"),
        D("Hay-like", "На сено"),
        D("Faint or absent", "Слаб или отсутен"),
    ]),
    ("Texture", "Текстура", [
        O("Dry, brittle", "Сува, кршлива"),
        O("Dry, resilient", "Сува, еластична"),
        O("Sticky, resinous", "Леплива, смолеста"),
        D("Slightly moist", "Малку влажна"),
        D("Damp", "Влажна"),
    ]),
    ("Visible defects", "Видливи недостатоци", [
        O("None observed", "Не се забележани"),
        D("Mould, mildew", "Мувла"),
        D("Discolouration", "Промена на бојата"),
        D("Insect damage", "Оштетување од инсекти"),
        D("Seeds present", "Присутни семки"),
        D("Excess stalk", "Вишок стебленца"),
    ]),
]

# ---------------------------------------------------------------------------
# #2 · Identification B · Microscopic · Ph. Eur. 2.8.23
# ---------------------------------------------------------------------------
MICROSCOPY = [
    ("Diagnostic structures", "Дијагностички структури", [
        O("Covering trichomes with cystoliths", "Покривни трихоми со цистолити"),
        O("Unicellular curved covering trichomes", "Еднокелични свиткани покривни трихоми"),
        O("Capitate-sessile glandular trichomes", "Главичести седечки жлездени трихоми"),
        O("Capitate-stalked glandular trichomes", "Главичести стебленести жлездени трихоми"),
        O("Bulbous glandular trichomes", "Меурести жлездени трихоми"),
        O("Calcium oxalate cluster crystals", "Друзи од калциум оксалат"),
        O("Anomocytic stomata", "Аномоцитни стоми"),
        O("Epidermis with striated cuticle", "Епидермис со набраздена кутикула"),
        O("Spiral and annular vessels", "Спирални и прстенести садови"),
        O("Sclerenchyma fibres", "Склеренхимски влакна"),
        O("Pollen grains", "Полен зрнца"),
        O("Bract and bracteole fragments", "Фрагменти од брактеи"),
    ]),
    ("Foreign structures", "Туѓи структури", [
        O("None observed", "Не се забележани"),
        D("Starch granules", "Скробни зрнца"),
        D("Fungal hyphae, spores", "Габични хифи, спори"),
        D("Structures of another species", "Структури од друг вид"),
    ]),
    ("Mount", "Препарат", [
        O("Chloral hydrate R", "Хлорал хидрат Р"),
        O("Lactic acid", "Млечна киселина"),
        O("Glycerol 50 %", "Глицерол 50 %"),
    ]),
    ("Magnification", "Зголемување", [
        O("× 40", "× 40"),
        O("× 100", "× 100"),
        O("× 400", "× 400"),
    ]),
]

# ---------------------------------------------------------------------------
# #7 · Foreign matter · Ph. Eur. 2.8.2 · in-house
# ---------------------------------------------------------------------------
FOREIGN_MATTER = [
    ("Categories found", "Најдени категории", [
        O("None detected", "Не е откриено"),
        D("Leaves > 1 cm", "Листови > 1 cm"),
        D("Stems and stalks", "Стебла и стебленца"),
        D("Seeds", "Семки"),
        D("Other parts of the plant", "Други делови од растението"),
        D("Foreign organic matter", "Туѓа органска материја"),
        D("Foreign inorganic matter", "Туѓа неорганска материја"),
        D("Insects, animal matter", "Инсекти, животинска материја"),
        D("Mould, decayed material", "Мувла, распаднат материјал"),
        D("Packaging fragments", "Фрагменти од амбалажа"),
    ]),
]

# The gravimetric lines of Ph. Eur. 2.8.2 — filled in at the bench, against the
# specification's own limit. (label_en, label_mk, unit, prefilled)
FM_MEASURE = [
    ("Sample mass", "Маса на примерок", "g", ""),
    ("Foreign matter", "Страни материи", "g", ""),
    ("Result", "Резултат", "% m/m", ""),
    ("Limit", "Граница", "", "≤ 2.0 %"),
]

# Which menu belongs to which determination of the certificate of quality.
BY_DET = {"1": MACROSCOPY, "2": MICROSCOPY, "7": FOREIGN_MATTER}

TITLES = {
    "1": ("Macroscopic Examination", "Макроскопско испитување", "Ph. Eur. mon. 3028"),
    "2": ("Microscopic Examination", "Микроскопско испитување", "Ph. Eur. 2.8.23"),
    "7": ("Foreign Matter", "Страни материи", "Ph. Eur. 2.8.2 · in-house"),
}


def census():
    out = []
    for det in ("1", "2", "7"):
        groups = BY_DET[det]
        n = sum(len(g[2]) for g in groups)
        dev = sum(1 for g in groups for o in g[2] if o.dev)
        out.append("#%-2s %-24s %2d groups  %3d options  %2d deviations"
                   % (det, TITLES[det][0], len(groups), n, dev))
    return out


def main(argv):
    for line in census():
        print(line)
    for det in ("1", "2", "7"):
        print("\n#%s %s" % (det, TITLES[det][0]))
        for en, mk, opts in BY_DET[det]:
            print("  %s | %s" % (en, mk))
            for o in opts:
                print("      %s %-40s %s" % ("!" if o.dev else " ", o.en, o.mk))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
