#!/usr/bin/env python3
"""Builds QASOP_0XX_A02 (Transport Validation Protocol) and QASOP_0XX_A05 (Transport Validation
Report) with the pp-document-suite engine: cover page, TOC, native equations (MKT), execution
forms with a two-role sign-off after every record step.

No result is printed: the protocol is executed on paper (A03/A04), and the report is a template
whose figures must be computed from the bound logger data (SKILL §6B) — nothing here is invented.

Usage: python3 build_validation.py <out_dir>
"""
import os, sys
ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pp-document-suite", "scripts")
sys.path.insert(0, os.path.abspath(ENGINE))
import pp_format as pf
import pp_report as pr

OUT = sys.argv[1] if len(sys.argv) > 1 else "docx"
SOP = "QASOP_0XX"

def roles(d, mk="Потпис за овој запис", en="Signature for this record"):
    """Two-role sign-off for one record step: the validation team member who executed it and
    entered the raw data, and QA who checked it (transport validation is QA-owned, QASOP_0XX §3)."""
    pr.entry_table(d, ["Улога | Role", "Име | Name", "Датум | Date", "Потпис | Signature"],
                   ["Извршил и внел сурови податоци (тим за валидација) | Executed & entered raw data (validation team)",
                    "Проверил и одобрил овој запис (QA) | Checked & approved this record (QA)"],
                   [9.46, 3.5, 2.0, 3.5], label_mk=mk, label_en=en)

def info(lane_label):
    return [("Код на рутата | Lane code", "L__"),
            ("Место на испраќање | Dispatch point", "Којлија 1043, Петровец | Kojlija 1043, Petrovec"),
            ("Место на прием | Receipt point", ""),
            ("Возило / конфигурација на палети | Vehicle / pallet configuration", ""),
            ("Опсег | Range", ""),
            ("План за валидација | Validation plan", "QASOP_0XX_A01 — ______"),
            ("Поврзана СОП | Governing SOP", "QASOP_0XX; WHSOP_003"),
            (lane_label, "TVP-___-__")]

APPROVAL = [("Изготвил | Prepared (тим за валидација | validation team)", ""),
            ("Прегледал | Reviewed (Логистика / Обезбедување | Logistics / Security)", ""),
            ("Одобрил | Approved (QA)", "")]

def doc(code, mk, en):
    return pf.new_annex(code=code, version="01", mk_title=mk, en_title=en, status="draft")

# ------------------------------------------------------------------ equations (shared)
MEAN = r"\bar{T}=\frac{1}{n}\sum_{i=1}^{n}T_i"
SD = r"s=\sqrt{\frac{\sum_{i=1}^{n}\left(T_i-\bar{T}\right)^2}{n-1}}"
MKT = r"T_K=\frac{\Delta H/R}{-\ln\left(\frac{1}{n}\sum_{i=1}^{n}e^{-\frac{\Delta H/R}{T_i}}\right)},\quad \Delta H/R=10000\,\mathrm{K}"
MKT_C = r"MKT=T_K-273{,}15"
TOUT = r"t_{out}=\Delta t\cdot\sum_{i=1}^{n}\mathbf{1}\left[T_i\notin\left[T_{min},T_{max}\right]\right]"

def equations(d):
    pr.body(d, "Сите вредности се пресметуваат од необработените податоци на секој логер (n мерења во интервал Δt), а не се читаат од софтверот без проверка; температурите во MKT се во келвини (T = °C + 273,15).",
            "All values are calculated from each logger's raw data (n readings at interval Δt), not read from the software without verification; temperatures in the MKT are in kelvin (T = °C + 273.15).")
    pr.minilabel(d, "Средна вредност", "Mean"); pr.eqn(d, MEAN)
    pr.minilabel(d, "Стандардна девијација (примерок)", "Standard deviation (sample)"); pr.eqn(d, SD)
    pr.minilabel(d, "Средна кинетичка температура (USP ⟨1079.2⟩)", "Mean kinetic temperature (USP ⟨1079.2⟩)"); pr.eqn(d, MKT); pr.eqn(d, MKT_C)
    pr.minilabel(d, "Кумулативно време надвор од опсег", "Cumulative time out of range"); pr.eqn(d, TOUT)

# ================================================================== A02 PROTOCOL
def protocol():
    code = SOP + "_A02"
    mk, en = "Протокол за валидација на транспорт (OQ/PQ)", "Transport Validation Protocol (OQ/PQ)"
    d = doc(code, mk, en)
    pr.cover_page(d, mk, en, info("Број на протокол | Protocol No."), kind_mk="ПРОТОКОЛ", kind_en="PROTOCOL",
                  study_mk="Квалификација на транспортна рута", study_en="Transport lane qualification",
                  approval_rows=APPROVAL, status="draft", version="01")
    pr.toc_page(d)

    pr.chapter(d, "1", "ЦЕЛ И ОПСЕГ", "Purpose and Scope")
    pr.body(d, "Овој протокол ги дефинира однапред тестовите, позициите на логерите, пресметките и критериумите за прифаќање со кои се квалификува наведената рута според QASOP_0XX. Протоколот мора да биде одобрен од QA пред почетокот на OQ; ниту еден критериум не се менува по почетокот на извршувањето без контрола на промени.",
            "This protocol pre-defines the tests, logger positions, calculations and acceptance criteria by which the stated lane is qualified per QASOP_0XX. The protocol must be approved by QA before OQ starts; no criterion is changed after execution starts without change control.")
    pr.body(d, "Опфатени фази: OQ — температурно мапирање на возилото/пакувањето (тестови OQ-1 до OQ-6); PQ — три последователни пратки (PQ-1 до PQ-3).",
            "Stages covered: OQ — temperature mapping of the vehicle/packaging (tests OQ-1 to OQ-6); PQ — three consecutive shipments (PQ-1 to PQ-3).")

    pr.chapter(d, "2", "ПРЕДУСЛОВИ", "Prerequisites")
    pr.entry_table(d, ["Предуслов | Prerequisite", "Референца | Reference", "Да | Yes", "Не | No"],
                   ["QASOP_0XX и WHSOP_003 одобрени | QASOP_0XX and WHSOP_003 approved",
                    "План за валидација и FMEA (A01) одобрени | Validation plan and FMEA (A01) approved",
                    "Возилото идентификувано; активна или пасивна заштита утврдена | Vehicle identified; active or passive protection established",
                    "Техничка документација за контролата на температура (ако постои) | Temperature-control technical documentation (if fitted)",
                    "10 USB логери калибрирани (≤ ±0,5 °C, ≤ ±3 % RH), софтверот верификуван | 10 USB loggers calibrated (≤ ±0.5 °C, ≤ ±3 % RH), software verified",
                    "Логери за еднократна употреба: сертификат на серијата, рок на употреба | Single-use loggers: lot certificate, expiry date",
                    "Палети, картони, стреч-фолија и термо-ќебиња во рутинската конфигурација | Pallets, cartons, stretch film and thermal blankets in the routine configuration",
                    "Тимот обучен за QASOP_0XX и WHSOP_003 | Team trained on QASOP_0XX and WHSOP_003",
                    "Симулираниот товар дефиниран (кеси со иста маса, G 8 / M 4 картони) | Simulated load defined (bags of the same mass, L 8 / S 4 cartons)"],
                   [9.46, 4.0, 2.5, 2.5])
    roles(d)

    pr.chapter(d, "3", "КОНФИГУРАЦИЈА НА ЛОГЕРИТЕ", "Logger Configuration")
    pr.body(d, "USB логери (10): P1–P8 во аглите на товарниот простор (P3, P4, P7, P8 кон вратите), P9 во центарот, P10 надвор (амбиент, во сенка); интервал 1 мин (OQ), 5 мин (PQ). Логери за еднократна употреба во тестовите со товар: по 2 во секоја палета — Е1 горен слој, аголот кон вратите; Е2 долен слој, центар (QASOP_0XX §6.4.2). Сите логери се синхронизираат по време пред почетокот.",
            "USB loggers (10): P1–P8 at the corners of the load space (P3, P4, P7, P8 towards the doors), P9 at the centre, P10 outside (ambient, shaded); interval 1 min (OQ), 5 min (PQ). Single-use loggers in the loaded tests: 2 in every pallet — E1 top layer, corner facing the doors; E2 bottom layer, centre (QASOP_0XX §6.4.2). All loggers are time-synchronised before the start.")
    pr.entry_table(d, ["Позиција | Position", "Сериски број | Serial No.", "Калибрација важи до | Calibration due", "Синхронизиран | Synchronised"],
                   ["P1–P4 горе | top", "P5–P8 долу | bottom", "P9 центар | centre", "P10 амбиент | ambient", "Е1 по палета | E1 per pallet", "Е2 по палета | E2 per pallet"],
                   [4.5, 5.0, 4.96, 4.0])
    roles(d)

    pr.chapter(d, "4", "КРИТЕРИУМИ ЗА ПРИФАЌАЊЕ", "Acceptance Criteria")
    t = d.add_table(rows=1, cols=3); t.alignment = pr.WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Тест | Test", "Критериум | Criterion", "Основа | Basis"]):
        pr.cellfmt(t.cell(0, j), h, None, 9, pr.WHITE, bold=True, fill=pr.NAVYF)
    CRIT = [("OQ-1 Празно | Empty", "Профил на воздухот наспроти амбиентот; кај активна: сите точки во опсег по стабилизацијата | Air profile against ambient; with active control: all points within range after stabilisation", "WHO TRS 961 Ann. 9 Suppl. 7"),
            ("OQ-2 Полно | Loaded", "Сите логери во палетите (Е1, Е2) во опсег ≥ 125 % од максималното времетраење; MKT во опсег | All pallet loggers (E1, E2) within range for ≥ 125 % of maximum duration; MKT within range", "Annex 15 §6; GDP 9.2"),
            ("OQ-3 Врата | Door", "Враќање во опсег ≤ 15 мин по секое отворање (2 × 5 мин) | Return to range ≤ 15 min after each opening (2 × 5 min)", "A01 FMEA"),
            ("OQ-4 Прекин | Power off", "Само активна: време на задржување ≥ макс. предвиден прекин (≥ 60 мин) | Active only: hold time ≥ max. foreseen interruption (≥ 60 min)", "A01 FMEA"),
            ("OQ-5/6 Сезона | Season", "Летно (амбиент ≥ 30 °C) и зимско (≤ 0 °C) мапирање: логерите во палетите во опсег | Summer (ambient ≥ 30 °C) and winter (≤ 0 °C) mapping: pallet loggers within range", "GDP 9.2; Suppl. 14"),
            ("PQ-1…3", "Сите логери во палетите во опсег; времетраење ≤ квалификуваното; пломби, завиткување и ланец на надзор комплетни | All pallet loggers within range; duration ≤ qualified; seals, wrapping and chain of custody complete", "Annex 15 §6; WHSOP_003")]
    for r in CRIT:
        c = t.add_row().cells
        for j, x in enumerate(r): pr.cellfmt(c[j], x, None, 9, pr.BLACK, fill=(pr.LBL if j == 0 else None))
    pr.fixed(t, [3.4, 11.06, 4.0]); pr.borders(t)
    pr.note(d, "Опсег за готов производ и меѓупроизвод: 15–25 °C, RH ≤ 60 %; клонови: +2 до +8 °C; семе: 5–20 °C (WHSOP_003 §6.1).",
            "Range for finished product and intermediate: 15–25 °C, RH ≤ 60 %; clones: +2 to +8 °C; seeds: 5–20 °C (WHSOP_003 §6.1).")

    pr.chapter(d, "5", "ПРЕСМЕТКИ", "Calculations")
    equations(d)

    pr.chapter(d, "6", "OQ — ИЗВРШУВАЊЕ", "OQ — Execution")
    pr.body(d, "Секој тест се изведува по редот, се евидентира во QASOP_0XX_A03 и се потпишува веднаш по завршувањето. Ако критериум не е исполнет, се постапува според §8.",
            "Each test is executed in order, recorded in QASOP_0XX_A03 and signed immediately on completion. If a criterion is not met, proceed per §8.")
    OQ = [("6.1", "OQ-1 Празно возило — стабилизација", "OQ-1 Empty vehicle — stabilisation",
           "Празен товарен простор, вратите затворени; кај активна контрола вклучи ја и бележи до стабилизација и уште 60 мин; кај пасивна бележи најмалку колку најдолгото патување.", "Empty load space, doors closed; with active control switch it on and record until stable and a further 60 min; with passive protection record for at least the longest journey."),
          ("6.2", "OQ-2 Полно возило", "OQ-2 Loaded vehicle",
           "Натовари палети со симулиран товар во максималната конфигурација, завиткани како во рутина, со Е1 и Е2 во секоја палета (вклучи најмалку една мала палета); затвори; бележи ≥ 125 % од максималното времетраење од A01.", "Load pallets with the simulated load in the maximum configuration, wrapped as in routine, with E1 and E2 in every pallet (include at least one small pallet); close; record for ≥ 125 % of the maximum duration from A01."),
          ("6.3", "OQ-3 Отворање на врата", "OQ-3 Door opening",
           "При полн товар, отвори ја вратата 5 мин, затвори, почекај враќање во опсег; повтори втор пат.", "With full load, open the door for 5 min, close, wait for return to range; repeat a second time."),
          ("6.4", "OQ-4 Прекин на напојување (само активна)", "OQ-4 Power interruption (active only)",
           "При полн товар во стабилна состојба, исклучи ја контролата на температура; бележи до првото излегување од опсегот (време на задржување); вклучи ја повторно. Кај пасивна заштита — N/A (времето на задржување го даваат OQ-2, OQ-5 и OQ-6).", "With full load at steady state, switch off temperature control; record until the first point leaves the range (hold time); switch back on. With passive protection — N/A (hold time is given by OQ-2, OQ-5 and OQ-6)."),
          ("6.5", "OQ-5 Летно мапирање", "OQ-5 Summer mapping",
           "Повтори го OQ-2 при амбиент ≥ 30 °C.", "Repeat OQ-2 at ambient ≥ 30 °C."),
          ("6.6", "OQ-6 Зимско мапирање", "OQ-6 Winter mapping",
           "Повтори го OQ-2 при амбиент ≤ 0 °C.", "Repeat OQ-2 at ambient ≤ 0 °C.")]
    for num, tmk, ten, pmk, pen in OQ:
        pr.subsec(d, num, tmk, ten)
        pr.body(d, pmk, pen)
        pr.entry_table(d, ["Почеток | Start", "Крај | End", "Мин. °C / поз. | Min. °C / pos.", "Макс. °C / поз. | Max. °C / pos.", "MKT °C", "Надвор (мин) | Out (min)", "Исполнет | Met"],
                       1, [2.4, 2.4, 3.0, 3.0, 2.2, 2.6, 2.86])
        roles(d)

    pr.chapter(d, "7", "PQ — ИЗВРШУВАЊЕ", "PQ — Execution")
    pr.body(d, "PQ започнува само по писмено одобрение на OQ од QA. Секоја пратка се изведува целосно според WHSOP_003 и се евидентира во QASOP_0XX_A04; барем една пратка мора да биде во сезоната на најлош случај.",
            "PQ starts only after written QA approval of OQ. Each shipment is performed in full per WHSOP_003 and recorded in QASOP_0XX_A04; at least one shipment must fall in the worst-case season.")
    pr.entry_table(d, ["Пратка | Shipment", "UTID", "Датум | Date", "Палети G/M | Pallets L/S", "Палети мин./макс. °C | Pallets min./max. °C", "MKT °C", "Траење | Duration", "Исполнет | Met"],
                   ["PQ-1", "PQ-2", "PQ-3"], [2.0, 2.8, 2.0, 2.0, 2.8, 1.8, 2.2, 2.86])
    roles(d)

    pr.chapter(d, "8", "ОТСТАПУВАЊА", "Deviations")
    pr.body(d, "Резултат надвор од критериумот прво се проверува (дефект на логер, поставување); ако се потврди, се отвора отстапување според QAS-05-002 и засегнатиот тест се повторува во целост по корекцијата. Ниеден резултат не се отфрла без образложение одобрено од QA.",
            "A result outside the criterion is first checked (logger failure, placement); if confirmed, a deviation is opened per QAS-05-002 and the affected test is repeated in full after correction. No result is discarded without a QA-approved justification.")
    pr.entry_table(d, ["Тест | Test", "Опис | Description", "Отстапување бр. | Deviation No.", "Решение | Resolution", "Повторено | Repeated"],
                   2, [2.0, 6.46, 3.0, 4.5, 2.5])

    pr.chapter(d, "9", "ЗАВРШНО ПОТПИШУВАЊЕ НА ИЗВРШУВАЊЕТО", "Final Execution Sign-off")
    pr.entry_table(d, ["Дејство | Action", "Име | Name", "Датум | Date", "Потпис | Signature"],
                   ["Извршил (тим за валидација) | Executed (validation team)",
                    "Прегледал (QA) | Reviewed (QA)",
                    "Одобрил (QP) | Approved (QP)"],
                   [7.46, 4.5, 2.5, 4.0])
    path = os.path.join(OUT, code + ".docx"); pf.save(d, path); print("WROTE", path)

# ================================================================== A05 REPORT
def report():
    code = SOP + "_A05"
    mk, en = "Извештај за валидација на транспорт", "Transport Validation Report"
    d = doc(code, mk, en)
    pr.cover_page(d, mk, en, info("Број на извештај | Report No."), kind_mk="ИЗВЕШТАЈ", kind_en="REPORT",
                  study_mk="Квалификација на транспортна рута", study_en="Transport lane qualification",
                  approval_rows=APPROVAL + [("Одобрил | Approved (QP)", "")], status="draft", version="01")
    pr.toc_page(d)

    pr.chapter(d, "1", "РЕЗИМЕ", "Executive Summary")
    pr.body(d, "Рутата L__ е квалификувана / не е квалификувана за опсегот ______ врз основа на OQ (тестови OQ-1 до OQ-6) и PQ (три пратки), извршени според протоколот QASOP_0XX_A02 бр. ______. Сите бројки во овој извештај се пресметуваат од необработените податоци наведени во §2; ниедна не се внесува рачно без проверка.",
            "Lane L__ is qualified / is not qualified for the range ______ on the basis of OQ (tests OQ-1 to OQ-6) and PQ (three shipments) performed per protocol QASOP_0XX_A02 No. ______. Every figure in this report is calculated from the raw data listed in §2; none is entered by hand without verification.")

    pr.chapter(d, "2", "ПОДАТОЦИ И ПОТЕКЛО", "Data and Provenance")
    pr.body(d, "За секоја датотека од логер се евидентира потеклото (ALCOA+): име на датотеката, SHA-256, големина и датум на измена, сериски број на логерот и тестот.",
            "For every logger file the provenance is recorded (ALCOA+): file name, SHA-256, size and modification date, logger serial number and test.")
    pr.entry_table(d, ["Тест | Test", "Логер | Logger", "Датотека | File", "SHA-256", "Бајти | Bytes", "Изменета | Modified"],
                   6, [1.8, 2.2, 4.46, 4.5, 2.0, 3.5])

    pr.chapter(d, "3", "МЕТОДА НА ПРЕСМЕТКА", "Calculation Method")
    equations(d)
    pr.subsec(d, "3.1", "Решен пример (образец)", "Worked example (template)")
    pr.body(d, "За секој логер и тест, MKT се прикажува како решен чекор: општа формула, формулата со вредностите и резултатот. Полињата подолу се пополнуваат од податоците; не се внесуваат измислени вредности.",
            "For each logger and test the MKT is shown as a worked step: general formula, the formula with the values, and the result. The fields below are filled from the data; no invented values are entered.")
    pr.calc_step(d, "MKT — логер ___, тест ___", "MKT — logger ___, test ___",
                 formula=MKT,
                 substituted=r"T_K=\frac{10000}{-\ln\left(\frac{1}{n}\sum e^{-10000/T_i}\right)},\quad n=\_\_\_",
                 result=r"MKT=\_\_\_\,^{\circ}C", tag="")

    pr.chapter(d, "4", "РЕЗУЛТАТИ — OQ", "Results — OQ")
    pr.entry_table(d, ["Тест | Test", "Мин. °C / поз. | Min. °C / pos.", "Макс. °C / поз. | Max. °C / pos.", "Средна °C | Mean °C", "s", "MKT °C", "Надвор (мин) | Out (min)", "Резултат | Result"],
                   ["OQ-1", "OQ-2", "OQ-3", "OQ-4", "OQ-5", "OQ-6"], [1.6, 2.8, 2.8, 2.0, 1.4, 1.8, 2.2, 3.86])
    pr.entry_table(d, ["Параметар | Parameter", "Критериум | Criterion", "Резултат | Result", "Исполнет | Met"],
                   ["Контрола на температура: активна / пасивна | Temperature control: active / passive",
                    "Време до опсег (мин; само активна) | Time to range (min; active only)", "Враќање по врата 1 / 2 (мин) | Return after door 1 / 2 (min)",
                    "Време на задржување (мин) | Hold time (min)", "Жешка точка: воздух / палета | Hot spot: air / pallet", "Студена точка: воздух / палета | Cold spot: air / pallet",
                    "Рутинска позиција: USB логер | Routine position: USB logger", "Рутинска позиција: логер во палета | Routine position: pallet logger"],
                   [6.0, 5.0, 4.96, 2.5])

    pr.chapter(d, "5", "РЕЗУЛТАТИ — PQ", "Results — PQ")
    pr.entry_table(d, ["Пратка | Shipment", "UTID", "Сезона | Season", "Палети мин. °C | Pallets min. °C", "Палети макс. °C | Pallets max. °C", "MKT °C", "Траење | Duration", "Резултат | Result"],
                   ["PQ-1", "PQ-2", "PQ-3"], [2.0, 2.8, 2.0, 1.8, 1.8, 1.8, 2.4, 3.86])

    pr.chapter(d, "6", "ОТСТАПУВАЊА", "Deviations")
    pr.entry_table(d, ["Отстапување бр. | Deviation No.", "Тест | Test", "Причина | Root cause", "CAPA", "Влијание врз заклучокот | Impact on conclusion"],
                   2, [3.0, 1.8, 5.0, 3.5, 5.16])

    pr.chapter(d, "7", "ЗАКЛУЧОК И СТАТУС", "Conclusion and Status")
    pr.status_grid(d, ["QUALIFIED", "QUALIFIED со ограничувања | with limitations", "NOT QUALIFIED"], selected=None, ncols=3)
    pr.entry_table(d, ["Ограничување | Limitation", "Вредност | Value"],
                   ["Сезона | Season", "Максимално времетраење | Maximum duration", "Максимален товар: палети G / M | Maximum load: pallets L / S",
                    "Возило и заштита (активна / пасивна) | Vehicle and protection (active / passive)",
                    "Рутински позиции на логерите (USB / палета) | Routine logger positions (USB / pallet)", "Важи до (реквалификација) | Valid until (requalification)"],
                   [8.0, 10.46])
    pr.body(d, "По одобрението, QA ја внесува рутата во QASOP_0XX_A06 и ограничувањата се пренесуваат во TRA (WHSOP_003_A01).",
            "After approval, QA enters the lane in QASOP_0XX_A06 and the limitations are carried into the TRA (WHSOP_003_A01).")

    pr.chapter(d, "8", "ОДОБРУВАЊЕ НА ИЗВЕШТАЈОТ", "Report Approval")
    pr.entry_table(d, ["Дејство | Action", "Име | Name", "Датум | Date", "Потпис | Signature"],
                   ["Изготвил (тим за валидација) | Prepared (validation team)",
                    "Пресметките проверил (второ лице) | Calculations verified (second person)",
                    "Одобрил (QA) | Approved (QA)", "Одобрил (QP) | Approved (QP)"],
                   [7.46, 4.5, 2.5, 4.0])
    path = os.path.join(OUT, code + ".docx"); pf.save(d, path); print("WROTE", path)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    protocol(); report()
