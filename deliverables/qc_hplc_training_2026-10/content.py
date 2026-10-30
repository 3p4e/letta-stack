"""Course content: Shimadzu i-Series Cannabis Analyzer with LabSolutions DB.

Every step cites the manual page it comes from. Figure ids are crops made by crop2.py
(<manual>_<printed page>_<cluster>); PHOTO:<file> is a photograph of our own instrument screen.
Block types:
  ('h', text)                     sub-heading
  ('p', html)                     paragraph
  ('steps', [(text, fig|None), ...], src)   numbered procedure
  ('fig', fig, caption, width%)
  ('box', kind, title, html)     kind: gmp | lab | warn | tip
  ('table', header, rows)
"""

GS = 'LC Getting Started Guide 223-10811C'
OPG = 'LabSolutions DB Operators Guide 223-10821H'
SUG = 'LabSolutions DB System Users Guide 223-10815S'
IM = 'LabSolutions DB Installation & Maintenance Guide 223-10817AC'
TH = 'Data Acquisition & Processing Theory Guide 223-60090O'
VA = 'Shimadzu i-Series Virtual Advisor (ssi.shimadzu.com)'
TS = 'Shimadzu LC Troubleshooting Guide SSI-12-24'
WI = 'QCWI 001 v01'

MODULES = []

def module(no, title, goal, blocks):
    MODULES.append(dict(no=no, title=title, goal=goal, blocks=blocks))

# ---------------------------------------------------------------------------
module(1, 'The system, its files and its GMP status',
 'Name every module of the analyser and its job, recognise the four LabSolutions file types, and state what the qualification on file does and does not cover.',
[
 ('h', '1.1 What the analyser is'),
 ('p', 'The Cannabis Analyzer for Potency is a Shimadzu HPLC system with a photodiode-array (PDA) detector, '
       'controlled by <b>LabSolutions DB</b> on the laboratory PC. Whatever the hardware layout, the same five functions are present '
       '(' + GS + ', p. 4; ' + WI + ', §6):'),
 ('table', ['Module', 'What it does', 'What can go wrong (and shows in the data)'], [
   ['Pump (low-pressure gradient, lines A–D)', 'Draws mobile phase from up to four bottles, mixes them through a proportioning valve and delivers a constant flow (range 0.01–5.00 mL/min).', 'Air in a line, a dirty check valve, an open drain valve or a leak → wrong flow or wrong composition → retention times move, baseline drifts, pressure is low or does not follow the flow.'],
   ['Autosampler', 'Draws the set volume from the vial and injects it; rinses the needle between injections.', 'Air in the measuring pump, worn needle seal → uneven areas, carry-over.'],
   ['Column oven', 'Holds the column at the method temperature (our method: 50 °C).', 'Run started before the oven reaches its set point → retention times differ.'],
   ['PDA detector (D2 lamp, 190–800 nm)', 'Records the full UV-VIS spectrum every sampling interval; chromatograms are extracted at any wavelength (we quantify at 220 nm).', 'Old lamp (> ~2,000 h), bubbles or dirt in the flow cell → noise, drift, low intensity.'],
   ['PC + LabSolutions DB', 'Controls the modules, acquires and processes data, keeps the audit trail in an SQL database.', 'Shared log-ins, unsaved changes, data outside the database → data-integrity findings.'],
 ]),
 ('fig', 'GS_4_0', 'The modular system used in Shimadzu\'s tutorial (pump LC-40B XR, autosampler SIL-40C, column oven CTO-40C, detector SPD-40V, controller CBM-40lite). '
        'Our analyser integrates the same functions in one housing; the LabSolutions screens are the same.', 45),
 ('fig', 'PHOTO:c90319cd-image.jpg', 'Our instrument, [Data Acquisition] window, 30.10.2026: the flow path from the bottles (A = 0.1 % formic acid in water, B = 0.1 % formic acid in ACN, C and D unassigned, rinse solution) '
        'through pump, autosampler, oven and PDA, with the control buttons (Pump ON, Purge, Rinse, Oven ON, Lamp, Zero) and the Instrument Monitor (mode, pressure, oven temperature, lamp).', 90),
 ('box', 'lab', 'Our configuration (read from the screen on 30.10.2026 and from QCWI 001)',
  '<ul><li><b>Pump mode:</b> Low pressure gradient. A = 0.1 % formic acid in water; B = 0.1 % formic acid in acetonitrile; C and D not assigned.</li>'
  '<li><b>Method file:</b> <code>HighThroughput_PDAcal 31102025_novi RT 1103.lcm</code>; End Time 8.00 min; oven 50 °C; temperature limit 90 °C.</li>'
  '<li><b>QCWI 001 §6.3–6.4:</b> flow 1.5 mL/min reached by a ramp 0.5 → 1.0 → 1.5 mL/min; injection 5 µL; report format <code>CannabisAnalyzerQuantitationReport.lsr</code>.</li>'
  '<li><b>Room:</b> 4–35 °C with minimal variation during the day; humidity 20–85 % (QCWI 001 §6).</li></ul>'
  'Where the screen and the work instruction disagree (e.g. QCWI 001 names the method <code>HighThroughput_PDA.lcd</code>, which is not the file in use), the trainer records it and QA corrects the WI.'),
 ('h', '1.2 The four file types'),
 ('table', ['Extension', 'File', 'Contains'], [
   ['.lcm', 'Method file', 'Instrument parameters (flow, gradient, oven, detector), data-processing parameters, compound table, calibration curve.'],
   ['.lcb', 'Batch file', 'The Batch Table for sequential acquisition: one row per injection (vial, sample type, level, method, data file).'],
   ['.lcd', 'Data file', '"All-in-one": the chromatograms/3D PDA data plus a copy of the method, the batch row and the report format used. It is the <b>raw data</b>.'],
   ['.lsr', 'Report format file', 'The layout of printed reports.'],
 ]),
 ('p', 'Source: ' + GS + ', p. 5; ' + SUG + ', §3.3 (p. 107: data files are an all-in-one structure).'),
 ('h', '1.3 What is qualified, and what is not'),
 ('box', 'gmp', 'Qualification status (EU GMP Annex 15)',
  'The documents on file, <b>0008090850 IQ, OQ and EQR</b> (Shimadzu d.o.o., 20.02.2025), qualify the <b>LabSolutions DB software and its PC</b>: software version and integrity, '
  'date/time, failed-login detection, audit log, electronic signatures, archive/retrieve, calculation checks. They contain <b>no hardware test</b> '
  '(flow accuracy, gradient composition, oven temperature, wavelength accuracy, noise and drift, injection precision, carry-over) and there is no PQ. '
  'Annex 15 defines OQ as verification that equipment performs as intended throughout the anticipated operating ranges (Glossary; §3.10–3.13). '
  'This course trains people; it does not qualify the instrument. Until a hardware OQ is done, every analyst must treat the daily checks in Module 4 as mandatory.'),
])

# ---------------------------------------------------------------------------
module(2, 'Start-up, log-in and system configuration',
 'Switch the system on in the right order, log in under your own identity, open the right project and confirm the instrument is connected and Ready.',
[
 ('steps', [
   ('Check the connections. All units (pump, autosampler, column oven and detector) must be connected to the system controller. Then switch each instrument on.', 'GS_12_1'),
   ('Switch on the PC and printer, and double-click the LabSolutions icon. The [Login] sub-window opens.', None),
   ('Log in with <b>your own</b> User ID and password, then click [OK].', 'GS_13_0'),
   ('Select the project and click [OK]. (At first log-in the project selection window opens automatically; afterwards the last project opens.)', 'GS_13_1'),
   ('In [LabSolutions Main], under [Instruments], double-click the instrument icon. The [Realtime Analysis] program opens.', 'GS_13_2'),
   ('Open the [Data Acquisition] window from the [Main] assistant bar.', 'GS_14_0'),
   ('Confirm the status display reads <b>[Ready]</b>. If it reads [Not Connected]: check the power, check the cables, check the system configuration (next steps).', 'GS_14_1'),
 ], GS + ', pp. 12–14; ' + OPG + ', pp. 9–10'),
 ('h', 'If the status is [Not Connected]: re-set the system configuration'),
 ('steps', [
   ('Open the [System Configuration] sub-window from the [Main] assistant bar.', 'GS_15_0'),
   ('Click [Instrument], select the system controller, choose the communication ([RS-232C] or [Ethernet] with the IP address) and click [Search] to list the connected modules. For a PDA, select the model on the [PDA] row.', 'GS_16_0'),
   ('Enter the IP address and confirm with [OK].', 'GS_16_1'),
   ('Check that the configuration is correct; double-click a unit to set its properties; click [OK] to send the settings to the LC.', 'GS_16_2'),
 ], GS + ', pp. 15–16; ' + IM + ', §3.1 and §3.4 (p. 37, p. 59)'),
 ('box', 'gmp', 'One person, one log-in',
  'QCWI 001 §6.1 says "enter <i>Admin</i> or your User ID". A shared Admin account makes every entry in the audit trail anonymous and is a data-integrity finding '
  '(EU GMP Annex 11 §12 Security, §9 Audit trails). Analysts log in only with their personal ID; the Admin account is for the system administrator, '
  'and only for administration. QA to correct the WI.'),
 ('box', 'warn', 'Changing the system configuration',
  'Changing the system configuration changes a qualified computerised system. It needs change control (Annex 15 Principle; Annex 11 §10) and is recorded in the log. '
  'Analysts do not change it; they call the system administrator.'),
])

# ---------------------------------------------------------------------------
module(3, 'The [Data Acquisition] window and the method',
 'Read every part of the [Data Acquisition] window, set or check the instrument parameters, send them to the instrument, and know which changes are saved and which are not.',
[
 ('h', '3.1 Anatomy of the window'),
 ('fig', 'OPG_11_0', '[Data Acquisition] window. 1 Toolbars (Standard, Data Acquisition, Instrument Control, LC Control, PDA Control). 2 [Chromatogram View]: chromatograms and status curves. '
        '3 [Instrument Monitor]: status and settings. 4 [Download]: transfers the parameters to the instrument. 5 [Instrument Parameters View]. 6 Full-screen switch.', 80),
 ('p', 'Source: ' + OPG + ', §2.1.2, p. 11.'),
 ('h', '3.2 Set the instrument parameters'),
 ('steps', [
   ('In [Instrument Parameters View], click [Normal], then the [Simple Settings] tab. Set the [LC Stop Time], pump flow and initial concentration, oven temperature and detector wavelength. '
    '[Apply to All acquisition time] sets every detector\'s End Time to the LC Stop Time.', 'GS_18_1'),
   ('Click the [LC Time Prog.] tab for a gradient: enter [Time], [Module], [Command], [Value]. [Draw curve] plots the program. The time counts from the start of the analysis (minimum 0.01 min).', 'OPG_13_0'),
   ('Click [Save Method File As] on the [File] menu, enter the file name and click [Save].', 'OPG_13_2'),
   ('Click [Download] to transfer the parameters to the instrument.', 'GS_19_1'),
 ], OPG + ', §2.2.1, pp. 12–13; ' + GS + ', pp. 18–19'),
 ('box', 'lab', 'Our rule',
  'Analysts do <b>not</b> create or edit the routine method. They load the approved method (next step) and check it against QCWI 001 before every run. '
  'A method change is a change to a validated test procedure (EU GMP Part I, 6.15) and goes through change control.'),
 ('steps', [
   ('To load the approved method: in the [Data Explorer], right-click and choose [Get the file from database], select the method and click [OK] (or drag the method file onto the [Data Acquisition] window).', 'GS_19_2'),
   ('Check the parameters on screen, then click [Download].', None),
   ('Click [Instrument On/Off] on the toolbar. Pump delivery and oven temperature control start.', None),
 ], GS + ', p. 19; ' + OPG + ', §2.2.2, p. 14'),
 ('h', '3.3 The control panel and the control toolbars'),
 ('fig', 'GS_20_0', 'Switching [Instrument Parameters View] to the control panel ([Display Settings of Instrument Parameter View]).', 70),
 ('fig', 'GS_20_1', 'The control panel: instrument status and direct control of each module. Click to download the conditions and close.', 70),
 ('table', ['Button', 'What it does'], [
   ['Instrument On/Off', 'Starts or stops pump delivery and oven control together.'],
   ['Pump On/Off', 'Starts or stops solvent delivery.'],
   ['Purge autosampler', 'Purges the autosampler for the [Purge Time] on the [Autosampler] tab.'],
   ['Rinse autosampler', 'Rinses the autosampler and sampling needle.'],
   ['Oven On/Off', 'Starts or stops column oven control.'],
   ['Zero detector / Zero PDA', 'Sets the detector signal to zero.'],
   ['PDA Lamp On/Off', 'Switches the D2 lamp of the PDA.'],
 ]),
 ('p', 'Source: ' + OPG + ', §2.3.6, p. 25.'),
 ('fig', 'OPG_25_0', '[LC Control] and [PDA Control] toolbars.', 70),
 ('h', '3.4 The Instrument Monitor'),
 ('steps', [
   ('The [Instrument Monitor] shows the live status: mode, pressure, flow, B concentration, oven temperature, room temperature, lamp. If hidden, click [Toggle Instrument Monitor].', 'OPG_26_1'),
   ('A value typed into the [Setting] column (e.g. a new flow) changes the instrument immediately.', None),
 ], OPG + ', §2.3.7, p. 26'),
 ('box', 'warn', 'A setting typed in the Instrument Monitor is not saved to the method',
  'The manual is explicit: a value changed in the [Setting] column is <b>not saved to the method file</b>; the change is only recorded in the operation log (Log Browser). '
  'On 30.10.2026 the monitor showed <b>1.0000 mL/min and 70 % B</b> while a run was in progress (2.62 / 8.00 min), although QCWI 001 gives 1.5 mL/min. '
  'Never acquire data while the flow is being ramped by hand. Ramp, wait until the oven and pressure are stable, then start the run with the method values.'),
 ('fig', 'PHOTO:3c59d033-image.jpg', 'Our Instrument Monitor on 30.10.2026 during a run: pressure 43 bar, flow 1.0000 mL/min, B 70.0 %, oven 44.9 / 50 °C (not yet at set point), room 21.4 °C.', 80),
 ('h', '3.5 Watch pressure, oven and room temperature as curves'),
 ('steps', [
   ('Right-click on the graph in [Chromatogram View] and click [Display Settings].', None),
   ('On the [Status] tab select the curves to draw: [Pump Press.], [Oven Temp.], [Room Temp.], [Detector Cell Temp.]; set the range of each and choose which one uses the right-hand axis. Click [OK].', 'OPG_18_1'),
   ('The selected status curves are drawn with the chromatogram.', 'OPG_19_0'),
 ], OPG + ', §2.3.1, p. 18'),
 ('box', 'tip', 'Use this every day',
  'Display [Pump Press.] and [Room Temp.] permanently. A pressure trace that is flat, jumps, or does not follow the flow is the first sign of a pump or mobile-phase fault; '
  'the room-temperature curve settles any question about the air conditioning with data instead of opinion.'),
])

# ---------------------------------------------------------------------------
module(4, 'Preparing the system: mobile phase, purge, equilibration and checks',
 'Prepare and connect the mobile phase correctly for a low-pressure gradient pump, purge, bring the system to stable conditions, and prove it with the baseline check and the system check before any sample is injected.',
[
 ('h', '4.1 Mobile phase'),
 ('table', ['Check point', 'Why (manual)'], [
   ['Use HPLC-grade solvents and filter through 0.45 µm.', 'The pump suction filter has 10 µm pores; smaller particles clog the flow path and column (' + OPG + ', p. 33; p. 37).'],
   ['Degas the mobile phase.', 'Bubbles form on mixing and with pressure and temperature changes; they cause defective delivery and detector noise (p. 37).'],
   ['Bring the mobile phase to room temperature before use.', 'Otherwise the baseline drifts and bubbles form while it settles. Mixing water and organic solvent changes the temperature (p. 33).'],
   ['<b>Low-pressure gradient: fill the flow path of all four lines A–D.</b>', '"Air bubbles in the gradient valve or from the solvent delivery pump up to the gradient valve may cause the retention time to fluctuate or be uneven" (p. 33).'],
   ['Autosampler rinse solution: same as mobile phase, no salt.', 'It contacts the mobile phase in the high-pressure valve (p. 35).'],
   ['Rinse-port cap: use the cap without a hole with volatile acids (formic acid).', VA + ', Autosampler maintenance.'],
 ]),
 ('box', 'lab', 'Our lines C and D',
  'On 30.10.2026 lines C and D were shown unassigned (grey bottles). On a low-pressure gradient pump they must still be filled (e.g. with mobile phase A or 50 : 50 water/ACN) and purged, '
  'or air can enter through the proportioning valve. Record which solvent is in each line on the mobile-phase preparation record.'),
 ('h', '4.2 Changing the mobile phase'),
 ('steps', [
   ('Pour the new mobile phase into a clean beaker (about 200 mL). Take the suction filter out of the old bottle, put it in the beaker and shake it to rinse it.', None),
   ('Open the drain valve (turn counter-clockwise) and purge the pump (about 3 min).', None),
   ('Put the suction filter into the new bottle and purge again to replace the flow path up to the column.', None),
   ('<b>Close the drain valve.</b>', None),
   ('Connect the column and switch the oven on. Deliver at half the analytical flow; when the oven temperature is stable, go to the analytical flow.', None),
 ], OPG + ', p. 34'),
 ('box', 'warn', 'An open drain valve is the first suspect when the pressure does not rise',
  'Shimadzu\'s hardware troubleshooting for "The pressure does not rise": <b>Is the drain valve open? → Close it. Is liquid leaking from a flow-line connection? → Retighten; replace the fitting if it still leaks</b> (' + VA + ', Hardware problems).'),
 ('h', '4.3 Auto-purge the pump and autosampler'),
 ('p', 'Auto-purge runs in this order: pump → autosampler → purge at the initial concentration (for non-isocratic modes) → warm-up at low flow until the oven reaches its set point (' + OPG + ', §2.3.2, p. 19).'),
 ('steps', [
   ('Click the [Autopurge] tab in [Instrument Parameters View]. Select every line to purge in [Mobile Phase Name] (all four for our pump) and enter a [Purge Time] for each.', 'OPG_19_1'),
   ('Select [Autosampler] and enter its [Purge Time].', 'OPG_20_0'),
   ('Set [Warm-up]: [Wait time] and the low [Flow] to use until the oven is at temperature (0 min disables warm-up).', 'OPG_20_1'),
   ('Click [Save], then click [Autopurge] on the toolbar.', None),
 ], OPG + ', §2.3.2, pp. 19–21'),
 ('h', '4.4 Bring the system to analytical conditions, and prove the pump delivers'),
 ('steps', [
   ('Increase the flow stepwise as QCWI 001 §6.3 describes (0.5 → 1.0 → 1.5 mL/min over 3–4 min).', None),
   ('<b>At each step write down the pressure.</b> The pressure must rise roughly in proportion to the flow. If it stays the same, stop: the pump is not delivering (drain valve open, leak, air in the pump head, check valve).', None),
   ('Wait until the oven shows the set temperature (50.0 / 50) and the status is [Ready].', None),
   ('Switch the D2 lamp on at least 1 hour before analysis (1–1.5 h for high sensitivity).', None),
   ('Equilibrate the column with at least 10–20 column volumes of mobile phase.', None),
 ], WI + ' §6.3; ' + VA + ' (warm-up 1 h); ' + TS + ', pp. 14, 17'),
 ('box', 'lab', 'Acceptance range for start-up pressure',
  'The start-up pressure at 1.5 mL/min and 50 °C must be recorded daily in logbook QCLB 018 and compared with the value from the last good run. '
  'The acceptance range is to be set from those records by the Head of QC (no range exists today).'),
 ('h', '4.5 Baseline check'),
 ('steps', [
   ('Click [Baseline Check Parameters] on the [Method] menu of the [Data Acquisition] window.', 'OPG_21_0'),
   ('Set the noise calculation method, select [Noise] and [Drift], enter the time window and threshold for each, a [Maximum Time] for repeating the check and the [Failure Action] (used in a batch). Click [OK] and save.', 'OPG_21_1'),
   ('Click [Baseline Check] on the toolbar. The result appears when the measurement ends and is saved in the database.', 'GS_21_2'),
   ('Read the result: pass or fail with the noise and drift values.', 'OPG_22_0'),
 ], OPG + ', §2.3.3, pp. 21–22; ' + GS + ', p. 21'),
 ('h', '4.6 Slope test'),
 ('steps', [
   ('With a stable baseline (not during acquisition or PDA plotting), right-click on the graph in [Chromatogram View] and click [Slope Test].', 'OPG_22_1'),
   ('Click [Set to Parameter] to enter the value as the integration [Slope]; round it up (e.g. 1988 → 2000) and save.', 'OPG_22_2'),
 ], OPG + ', §2.3.4, pp. 22–23'),
 ('box', 'warn', 'Slope test and our method',
  'The slope value is part of the validated data-processing parameters. Do not change it on a routine run; the slope test is a method-development and investigation tool.'),
 ('h', '4.7 System check (consumables)'),
 ('steps', [
   ('Click [System Check] on the [Main] assistant bar.', None),
   ('Select [Consumables Check] and [LC Check]; under [Advanced] select the items; select [Report Out] to print. Click [Run].', 'OPG_23_0'),
   ('Click [View Results]. Results are saved as <code>SysChk#_YYYYMMDDHHMMSS.lcs</code>.', None),
 ], OPG + ', §2.3.5, pp. 23–24'),
 ('h', '4.8 Daily start-up checklist (record in QCLB 018)'),
 ('table', ['#', 'Check', 'Record'], [
   ['1', 'Bottles A–D: correct solvent, label, preparation date, enough volume; suction filters immersed.', 'Lot numbers, prep date'],
   ['2', 'Rinse solution present; rinse cap without hole (formic acid).', '✓'],
   ['3', 'Drain valve closed; no drops at fittings or in the leak tray.', '✓'],
   ['4', 'Auto-purge of all lines and the autosampler done.', 'Time'],
   ['5', 'Pressure at 0.5 / 1.0 / 1.5 mL/min rises with flow; value at 1.5 mL/min in range.', 'bar ×3'],
   ['6', 'Oven at 50.0 °C; status [Ready].', 'Time'],
   ['7', 'Lamp on ≥ 1 h; lamp hours below the replacement limit.', 'h'],
   ['8', 'Baseline check passed (noise, drift).', 'Values'],
   ['9', 'Room temperature (Instrument Monitor).', '°C'],
   ['10', 'Only then: start the batch (blank → standards → samples).', 'Initials, time'],
 ]),
])

# ---------------------------------------------------------------------------
module(5, 'Single run',
 'Acquire one chromatogram, including a run without injection, and know how to stop it or change its time.',
[
 ('steps', [
   ('Confirm [Ready] on the status display. Click [Single Run] on the [Acquisition] assistant bar.', 'GS_23_1'),
   ('Enter the sample information and the data file name; select [Auto-increment] so that no file is overwritten (e.g. TEST-001.lcd).', 'OPG_27_0'),
   ('Enter [Vial#] and [Injection Volume]. <b>Vial# −1 acquires data without injecting</b>, i.e. a system blank. Click [OK]; the run starts.', 'GS_24_0'),
   ('The status changes to [Running]; the [LabSolutions Service] tray icon flashes green. Do not switch off the PC while it flashes.', 'GS_24_1'),
 ], GS + ', pp. 23–24; ' + OPG + ', §2.4.1, pp. 27–28'),
 ('h', 'Stop a run, change its time, take a snapshot'),
 ('steps', [
   ('[Stop] on the [Acquisition] assistant bar ends the run early; a data file is created with the data so far.', None),
   ('[Change Acquisition Time] on the [Acquisition] menu changes the end time during the run; it is recorded in the operation log. [Apply to Method File] makes it permanent.', 'OPG_28_0'),
   ('[Snapshot] opens the data collected so far in [Data Analysis]; [Update for Snapshot] refreshes it.', None),
 ], OPG + ', §2.4.2–2.5, pp. 28–29'),
 ('box', 'warn', 'A data file longer than its method',
  'On 30.10.2026 the sample file <code>ZCAP082601_007.lcd</code> contained data to about 19–20 min while the method in use has End Time 8.00 min. '
  'Either another method acquired it or the time was changed. Every such change must be traceable in the operation log; a result is not reported until it is explained.'),
])

# ---------------------------------------------------------------------------
module(6, 'Realtime batch: the Batch Table',
 'Build, check, run, pause and stop a Batch Table with blanks, calibration standards and samples, and make the system stop itself if it is not suitable.',
[
 ('h', '6.1 Build a Batch Table with the wizard'),
 ('steps', [
   ('Open the [Realtime Batch] window from the [Main] assistant bar, then click [Wizard]. Click [New], enter the [Method File] and [Injection Volume] and the acquisition pattern of standards and unknowns.', 'OPG_66_0'),
   ('Enter the standard sample information: [Sample Name], [Sample ID], data file name, [Number of Calibration Levels], [Repetitions per Run]; tick [Clear all calibrations at the beginning] to start a new curve.', 'OPG_67_1'),
   ('Enter the unknown sample information the same way.', 'OPG_68_0'),
   ('Set the summary reports.', 'OPG_69_0'),
   ('Select the items to execute (Startup, Shutdown), set them, enter the batch file name and click [Finish].', 'OPG_70_0'),
 ], OPG + ', §4.2.1, pp. 65–71'),
 ('h', '6.2 Or edit the Batch Table directly'),
 ('steps', [
   ('Use the table easy-setting: set [Standard], vials, injection volume, repetitions and data file name, and click to create the rows; then add the unknowns. Enter "−1" in [Vial#] for a run without injection.', 'GS_32_1'),
   ('Copy a cell down, or enter a numbered series, to fill the remaining rows.', 'GS_33_0'),
   ('Enter the remaining items directly and save the batch file.', 'GS_34_1'),
   ('Alternatively use [Quick Batch]: enter sample information, select sample type and vials, add them to the table.', 'GS_35_1'),
 ], GS + ', pp. 31–35'),
 ('h', '6.3 Sample Type and Level — where our 30.10 run went wrong'),
 ('steps', [
   ('Click the [Sample Type] cell of the <b>first</b> standard, click [Standard] and select <b>[Initialize Calibration Curve]</b>. It shows as "1: Standard (I)".', 'OPG_105_0'),
   ('For each following standard select [Standard] and <b>[Add Calibration Level]</b>. It shows as "1: Standard". Unknowns keep "0: Unknown".', 'OPG_105_1'),
   ('Set the [Level#] of each standard to the level whose concentration is in the Compound Table. Level# is ignored for unknowns.', None),
   ('For unknowns enter [Sample Amt.] and [Dil. Factor] so that the result is calculated per gram of sample.', None),
 ], OPG + ', §4.6.2, pp. 103–108'),
 ('box', 'warn', 'Standards entered as "Unknown"',
  'On 15.09 and 30.10.2026 the standard STD_005 was acquired with Sample Type <b>Unknown</b>. No calibration curve was built from that day\'s standards; samples were quantified against whatever curve was stored in the method. '
  'QCWI 001 §6.4 already requires "Standard". Check the Sample Type column of every batch before you press Start.'),
 ('h', '6.4 Show the columns you need'),
 ('steps', [
   ('Right-click the Batch Table and choose [Table Style]. Move items between [Hide Items] and [Display Items] with [Add]/[Remove]; order them with [Up]/[Down]. Hidden items still run.', 'OPG_81_1'),
 ], OPG + ', §4.2.3, pp. 80–82'),
 ('p', 'Display at least: Sample Type, Level#, Vial#, Inj. Volume, Sample Amt., Dil. Factor, Method File, Data File, Baseline Check, System Suitability, Action.'),
 ('h', '6.5 Run, stop, pause'),
 ('steps', [
   ('Click [Start Realtime Batch]. The [Realtime Batch] and [Data Acquisition] windows open and acquisition starts at row 1.', 'GS_36_0'),
   ('To run only some rows, select them, click [Start Realtime Batch], tick [Selected Row(s)] and confirm.', None),
   ('[Stop]: choose [Data acquisition under execution] (skip to the next row), [Batch Processing] (stop after this run) or both (stop now).', 'OPG_85_0'),
   ('[Edit Table/Restart]: pause at a chosen row, edit the rows not yet acquired, save, and click [Edit Table/Restart] again to resume. Acquired rows cannot be edited.', 'OPG_86_0'),
 ], OPG + ', §4.3, pp. 84–87'),
 ('h', '6.6 Let the batch protect itself'),
 ('steps', [
   ('<b>Baseline check in the batch:</b> select [Baseline Check] in the first row; the batch waits until noise and drift pass, or follows the [Failure Action].', None),
   ('<b>Startup:</b> [Settings] → [Startup] tab: start the instruments at a set date and time with a [Pumping Period] at initial conditions before the first row.', 'OPG_89_0'),
   ('<b>Shutdown:</b> [Settings] → [Shutdown] tab: a shutdown method and a [Cool down Time] after the last row.', 'OPG_90_0'),
   ('<b>Bracket calibration:</b> [Settings] → [Bracket] tab: Overlap, Sequence or Average, so unknowns are calculated from the standards before and after them.', 'OPG_94_0'),
 ], OPG + ', §4.4, pp. 88–94'),
 ('h', '6.7 System suitability test (SST) that stops the batch'),
 ('steps', [
   ('Save the SST parameters in the method: load the method in [Data Acquisition] and open the system-suitability settings; for each compound add the check items (e.g. area repeatability %RSD, resolution, tailing, theoretical plates) with their limits. Up to 100 items.', 'SUG_121_1'),
   ('Set the display type, rounding and digits for each item. Resolution and tailing are calculated by the method chosen on the [Performance] tab.', 'SUG_124_0'),
   ('In the Batch Table, mark the SST injections and in the [Action] cell set: Test = [System Suitability], Result = [Fail], Action = [Stop (Wait Next Queue)].', 'SUG_126_1'),
 ], SUG + ', §4.1–4.3, pp. 121–126'),
 ('box', 'gmp', 'No SST criteria exist yet',
  'QCWI 001 defines no system-suitability criteria. Without them nobody can show a run was valid (EU GMP Part I 6.15, 6.17; Ph. Eur. 2.2.46). '
  'Proposed minimum, to be set and approved by the Head of QC from validation data: 5–6 replicate standard injections; %RSD of area and retention time; resolution of the critical pair d9-THC / d8-THC; tailing; plate count.'),
 ('h', '6.8 Summary report'),
 ('steps', [
   ('Add [Summary Type] and [Summary Report Format File] to the table display.', 'GS_37_0'),
   ('Set the summary report on the rows it covers (standards, unknowns).', 'GS_37_1'),
   ('Run the batch; the summary report prints at the end.', 'GS_38_1'),
 ], GS + ', pp. 37–39'),
 ('h', '6.9 The run order we use'),
 ('table', ['Row', 'Injection', 'Sample Type', 'Purpose'], [
   ['1', 'Vial −1 (no injection), with [Baseline Check]', 'Unknown', 'System blank: proves pump, mobile phase and detector before anything is injected.'],
   ['2', 'Diluent blank', 'Unknown', 'Carry-over and ghost peaks.'],
   ['3–n', 'Calibration standards, level 1 … k', 'Standard (I) then Standard', 'Builds the day\'s calibration curve.'],
   ['n+1…', 'SST replicate injections', 'per method', 'Suitability; batch stops on fail.'],
   ['…', 'Samples (with check standard every ~10)', 'Unknown', 'Results; bracket calibration if used.'],
   ['last', 'Check standard', 'per method', 'Drift over the batch.'],
 ]),
])

# ---------------------------------------------------------------------------
module(7, 'Data analysis: integration, identification, quantitation and column performance',
 'Open a data file, read the chromatogram and tables, and understand each data-processing parameter well enough to see when a result is not trustworthy.',
[
 ('h', '7.1 Open a data file'),
 ('steps', [
   ('Open the [Postrun Analysis] program from [LabSolutions Main] (right-click the instrument → [Postrun]) and select the instrument.', 'GS_25_1'),
   ('Open the [Data Analysis] window.', 'GS_25_2'),
   ('In the [Data Explorer] double-click (or drag) the .lcd file. The window shows [Chromatogram View], [Results View] and [Method View].', 'GS_26_0'),
 ], GS + ', pp. 25–26; ' + OPG + ', §6.1, pp. 129–130'),
 ('box', 'gmp', 'Processing changes only this file — until you save them to the method',
  'In [Data Analysis], parameter changes apply only to the data file open. To apply them to other data they must be exported to a method file and that method re-applied (' + OPG + ', §6.2, p. 134; §6.7, p. 174). '
  'Routine analysts do not change processing parameters; any reprocessing is done under the audit trail with a reason recorded.'),
 ('h', '7.2 Peak integration parameters'),
 ('fig', 'OPG_134_0', '[Method View] → [Integration] tab: Width, Slope, Drift, T.DBL, Min. Area/Height.', 60),
 ('table', ['Parameter', 'Meaning', 'Effect if wrong'], [
   ['Width', 'Minimum half-height width of a peak to detect. Narrower "peaks" are treated as noise.', 'Too large: small/narrow peaks missed. Too small: noise integrated.'],
   ['Slope', 'Baseline slope (µV/min) that defines peak start and end; from the slope test.', 'Too large: only sharp peaks; too small: noise detected as peaks.'],
   ['Drift', '0 = automatic baseline; a value sets the slope used to draw the baseline under unresolved peaks.', 'Wrong value: peaks split vertically instead of separated, or baseline drawn wrongly.'],
   ['T.DBL', 'Time at which Width and Slope are doubled (for broadening late peaks).', 'Late peaks under- or over-detected.'],
   ['Min. Area/Height', 'Peaks below this value are not reported.', 'Real small peaks suppressed.'],
 ]),
 ('p', 'Sources: ' + OPG + ', §6.2, pp. 134–135; ' + TH + ', §1.1, pp. 1–14 (Width, Slope, Drift, slope test; do not use the slope test for gradient runs with large drift).'),
 ('fig', 'GS_27_0', 'Entering Width and Slope and re-processing the data (Getting Started Guide example: Width 5 s, Slope 1000 µV/min).', 75),
 ('h', '7.3 Identification: how a peak gets its name'),
 ('fig', 'OPG_148_0', '[Identification] tab: Window/Band, identification method (Absolute Rt / Relative Rt), peak selection, retention time update.', 60),
 ('p', '<b>Window</b> (isocratic): the allowance grows with retention time, '
       '<code>± (Rt × window % / 100 + 0.02) min</code>. <b>Band</b> (gradient): a fixed allowance in minutes, per peak if needed. '
       '<b>Absolute Rt</b> counts from the start of the run; <b>Relative Rt</b> corrects using a reference peak (' + OPG + ', §6.3, p. 148; ' + TH + ', §1.3.1–1.3.2, pp. 25–26).'),
 ('box', 'warn', 'The software names whatever falls in the window',
  'If the chromatography shifts, a different compound can fall into a window and be reported under the wrong name, and the real compound is reported as "not detected". '
  'On 30.10.2026 CBDA and CBD were "found" at their usual times while d9-THC, d8-THC and THCA disappeared and three unnamed peaks appeared. '
  'Always compare retention times with the day\'s standards and use the PDA spectrum (Module 8) to confirm identity.'),
 ('h', '7.4 Quantitation by external standard'),
 ('steps', [
   ('In [Method View] → [Quantitative] tab select [External Standard] and enter [# of Calib. Levels].', 'OPG_151_0'),
   ('In the [Compound] tab enter the concentration of each level for each compound.', 'OPG_151_1'),
 ], OPG + ', §6.4.1, pp. 150–151; ' + TH + ', §1.4 and §2.1 (calibration curve types)'),
 ('h', '7.5 The Compound Table'),
 ('steps', [
   ('[Wizard] on the [Data Analysis] assistant bar: integration parameters → select peaks → quantitative parameters → identification parameters.', 'OPG_163_0'),
   ('Select the peaks to register in the Compound Table.', 'OPG_164_0'),
   ('Enter quantitative and identification parameters and finish.', 'OPG_164_2'),
   ('Or fill the table directly: name, type, retention time (click the peak to copy its Rt), concentrations. Click the button that turns edited cells yellow to fix them.', 'GS_29_1'),
 ], OPG + ', §6.5, pp. 163–164; ' + GS + ', p. 29'),
 ('h', '7.6 Column performance: plates, resolution, tailing'),
 ('steps', [
   ('[Method View] → [Performance] tab: tick the calculation method ([EP] for Ph. Eur.; USP, JP etc. also available), set the unretained peak time and the column length.', 'OPG_172_0'),
   ('[Results View] → [Peak Table] shows theoretical plates and resolution.', 'OPG_173_0'),
   ('To show the tailing factor: right-click the Peak Table → [Table Style], add [Tailing F.].', 'OPG_173_2'),
 ], OPG + ', §6.6, pp. 172–173; ' + TH + ', §3.3, pp. 57–64'),
 ('h', '7.7 Save to the method (method owner only)'),
 ('steps', [
   ('[File] → [Save Method File As] with the method selected; or [Apply to Method] on the assistant bar.', 'GS_30_2'),
 ], GS + ', p. 30; ' + OPG + ', §6.7, p. 174'),
])

# ---------------------------------------------------------------------------
module(8, 'PDA data analysis: contour, spectra, library and peak purity',
 'Use the 3D PDA data to confirm the identity and purity of a peak, and read a spectrum well enough to tell a cannabinoid from a baseline artefact.',
[
 ('h', '8.1 The [PDA Data Analysis] window'),
 ('fig', 'OPG_178_0', '[PDA Data Analysis] window: toolbar, [Contour View] (absorbance colour-coded over time and wavelength), [Spectrum View], [Purity View], [Method View], [Results View].', 80),
 ('p', 'Open it from the [PDA Data Analysis] icon on the [Main] assistant bar of [Postrun Analysis] and drag in the data file. '
       'Move the cursors in [Contour View] to extract the chromatogram at a wavelength and the spectrum at a time (' + OPG + ', §7.1, pp. 177–178).'),
 ('h', '8.2 Reading our own data'),
 ('fig', 'PHOTO:fe1f748d-image.jpg', 'Our sample ZCAP082601_007, spectrum at 2.62 min: maximum ~268 nm with a shoulder ~305 nm (the pattern of an acidic cannabinoid: THCA/CBDA/CBGA), '
        'but the trace falls far below zero under ~250 nm (background changed after the detector was zeroed), and a spike at ~656 nm (the D2 lamp emission line).', 80),
 ('table', ['What you see', 'What it means'], [
   ['Maxima near 270 nm and ~305–310 nm', 'Acidic cannabinoid (THCA, CBDA, CBGA). Neutral cannabinoids (THC, CBD, CBN) lack the ~305 nm band.'],
   ['Negative absorbance at low UV (< 250 nm)', 'Not an analyte. The mobile-phase background in the cell absorbs less than when the detector was zeroed: composition changed (formic acid / water / ACN). 220 nm results in that region are unreliable.'],
   ['Spike at 656 nm (or 486 nm)', 'Deuterium-lamp emission lines; prominent spikes point to low or unstable lamp energy. Check lamp hours and intensity (Module 11).'],
   ['Signal at ~430 nm', 'Chlorophyll and pigments (fresh/moist flower), not cannabinoids.'],
 ]),
 ('h', '8.3 Register spectra and compare them'),
 ('steps', [
   ('Right-click in [Spectrum View] → [Register Extracted Spectrum to Table]; then [Show Spectrum Table].', 'OPG_186_0'),
   ('In the Spectrum Table check [Data Source], [Param.] (the retention time) and [Scale]. To compare with a library spectrum, set [Data Source] = [Library] and choose the spectrum.', 'OPG_187_0'),
 ], OPG + ', §7.3, pp. 186–187'),
 ('h', '8.4 Build a cannabinoid UV library from our standards'),
 ('steps', [
   ('Open the [UV Library Editor] from the [Main] assistant bar of [Postrun Analysis] and click [New] to create the library file.', None),
   ('Register the spectrum of each cannabinoid from a good standard run (one per compound, with the retention time and standard lot in the comment).', 'OPG_187_2'),
   ('Use it to identify peaks by similarity: [Method View] → [Identification] → [Peak Selection] = [Similarity].', 'OPG_198_0'),
 ], OPG + ', §7.4–7.5, pp. 192–201'),
 ('h', '8.5 Peak purity'),
 ('steps', [
   ('[Method View] → [Purity] tab: wavelength range ([From]/[To]), [Step], and [Background Compensation] for drifting baselines.', 'OPG_204_0'),
   ('Select the peak in [Chromatogram View] and read [Purity View]: [Peak Purity] (spectral) and [Peak Profile] (chromatograms at several wavelengths).', 'OPG_205_0'),
 ], OPG + ', §7.6, pp. 204–205; ' + TH + ', §4, pp. 77–98'),
])

# ---------------------------------------------------------------------------
module(9, 'Many data files: Quant Browser, export and printing',
 'Review a whole batch at once, check calibration and identification across it, and export or print the results.',
[
 ('steps', [
   ('Open the [Browser] program (right-click the instrument → [Browser]) and the [Quant Browser] window.', None),
   ('Drag the batch file from the [Batch] tab of the [Data Explorer] onto the window; the method and all data files load.', 'GS_41_0'),
   ('Check the quantitative results of each compound in [Quantitative Results View]; the calibration curve shows on the right.', 'GS_42_0'),
   ('If peak detection is wrong, check the integration parameters and run postrun batch on all data (method owner only).', 'GS_43_0'),
   ('If peaks are not identified correctly, check the identification parameters and the Compound Table.', 'GS_44_0'),
   ('Check the calibration points and the curve: the first-level point must be in use.', 'GS_45_0'),
 ], GS + ', pp. 40–45; ' + OPG + ', §9, pp. 263–280'),
 ('steps', [
   ('Export: [File] → export the quantitative results; choose output file, [Items Displayed on the Screen], [All IDs].', 'GS_46_1'),
   ('Print: [File] → [Print Table]; [Edit Format] changes the layout.', 'GS_47_1'),
 ], GS + ', pp. 46–47'),
 ('box', 'gmp', 'Exports are copies, not records',
  'The record is the .lcd in the database with its audit trail. A text export, an Excel sheet or a photo of the screen is a copy; results are reported from the signed LabSolutions report (Annex 11 §7–8; EU GMP Part I 6.17).'),
])

# ---------------------------------------------------------------------------
module(10, 'Data management, security and data integrity',
 'Find, review and protect data; know the audit trail, reasons for change, user rights, screen lock, backup and the program-integrity check.',
[
 ('h', '10.1 Data Manager'),
 ('steps', [
   ('Open [DataManager] from [LabSolutions Main] → [Postrun] → [DataManager]; select [Data] for [Files of type].', 'GS_48_1'),
   ('Filter by instrument name, date, sample or method; check the data file names.', 'GS_50_0'),
   ('Click a data file to see its information; double-click its PDF report.', 'GS_50_1'),
 ], GS + ', pp. 48–53; ' + SUG + ', §2.2, pp. 48–63'),
 ('h', '10.2 Audit trail and reasons for change'),
 ('steps', [
   ('[File] → [Method File Properties] → [Audit Trail] tab: tick [Apply to the data file acquired with this method file] and [Input reason when saving file]. Once attached to a data file an audit trail can never be removed.', 'SUG_102_0'),
   ('When a file with this setting is saved after a change, LabSolutions lists what changed and will not close until a reason is entered.', 'SUG_106_0'),
   ('Data file [Properties] → [File Info.] (who created and modified it, unique File ID) and [Sample Info.] (acquisition data; editing Sample Amount / Dilution recalculates the result and is logged).', 'SUG_108_1'),
 ], SUG + ', §3.1–3.3, pp. 101–108'),
 ('h', '10.3 Who may do what'),
 ('steps', [
   ('Security policy: [LabSolutions Main] → [Administration Tools] → [Security Policy]: password length and expiry, lock-out after failed attempts, signature policy.', 'SUG_5_0'),
   ('Rights groups: each user belongs to a group whose rights (acquire, edit method, process, sign, administer) are set by the administrator.', 'SUG_12_1'),
   ('Leaving the PC: [Window] → [Lock]. The window minimises; your ID and password re-open it.', 'SUG_37_0'),
   ('Log Browser: filter the system, application and authentication logs by user, period and event (e.g. audit trail).', 'SUG_41_0'),
 ], SUG + ', §1.2–1.4, pp. 4–41'),
 ('h', '10.4 Backup and program integrity (administrator)'),
 ('steps', [
   ('[Backup]: select the project (and the logs), enter a reason, choose the destination. A reason is mandatory in ER/ES mode.', 'SUG_94_0'),
   ('[Validation] → [Check the Program Files] → [Execute]: compares the installed programs with the original installation.', 'SUG_135_1'),
 ], SUG + ', §2.5, pp. 93–94; §5.3, p. 135'),
 ('box', 'gmp', 'The rules behind these functions',
  'Annex 11: §7 data storage and backup; §9 audit trails, reviewed regularly; §12 security, individual access; §11 periodic evaluation. EU GMP Part I Chapter 4 (documentation) and 6.17 (test records). '
  'The audit trail of each batch is reviewed before the result is approved.'),
])

# ---------------------------------------------------------------------------
module(11, 'Maintenance: PDA utility, consumables and shut-down',
 'Run the PDA checks, reset consumable counters after a part change, recognise the periodic maintenance items and shut the system down correctly.',
[
 ('h', '11.1 PDA Utility (LC-2030/2040/2050/2060)'),
 ('table', ['When', 'Do'], [
   ['Detector installed or moved', 'Wavelength check (D2/Ho)'],
   ['Lamp replaced', 'Auto-set exposure time; reset lamp usage time; wavelength check'],
   ['Flow cell replaced', 'Auto-set exposure time; wavelength check'],
   ['Validation (OQ/requalification)', 'Wavelength check; leak sensor; linearity and accuracy of absorbance'],
 ]),
 ('p', 'Source: ' + IM + ', §4.2, p. 68. The wavelength check measures the D2 emission lines 486.0 and 656.1 nm and the holmium-filter maxima 287.6 and 360.8 nm (§4.3.2).'),
 ('steps', [
   ('Windows [Start] → [LabSolutions] → [Instrument Maintenance Tools]. In [Tool Launcher] select [PDA Utility (LC-2030/2040/2050/2060)] and the detector, click [Run].', 'IM_69_0'),
   ('Log in with a user who has the rights; the utility opens in Manager or Operator mode.', 'IM_69_1'),
   ('Choose the function: [Wavelength], [Linearity], [Check Temp.], [Leak Check], [Inst. Info.]. Fill the flow cell with water first where the utility asks.', 'IM_69_2'),
 ], IM + ', §4.2, pp. 68–69'),
 ('h', '11.2 Consumable counters'),
 ('steps', [
   ('After replacing a consumable: [System Check] → [Advanced>>] → [Reset] → [LC] tab → [Reset] for the item replaced.', 'IM_68_0'),
 ], IM + ', §4.1.1, pp. 65–68'),
 ('h', '11.3 Periodic maintenance items (i-Series)'),
 ('table', ['Part', 'When', 'Note'], [
   ['Plunger seal', 'Pressure unstable or leak between pump head and holder', 'Reset usage, purge, check stability'],
   ['Check valves (inlet/outlet)', 'System check fails / unstable delivery', 'Rinse or sonicate 5 min in 2-propanol; never disassemble; replace if still unstable'],
   ['Suction filters (pump, autosampler)', 'Bubbles in the suction tubing after purge', 'Sonicate in 2-propanol; replace'],
   ['Line filter', 'Pressure too high', 'Sonicate or replace'],
   ['Drain valve seal', 'Leaks / does not close', 'Replace'],
   ['Rinse solution (10 % 2-propanol, plunger rinse)', 'Weekly', 'Even if it looks clean'],
   ['D2 lamp', '> ~2,000 h or low intensity', 'Then PDA utility steps above'],
   ['Needle, needle seal, HPV rotor/stator', 'Carry-over, leaks, scratches', 'Condition after replacement'],
 ]),
 ('p', 'Source: ' + VA + ', Periodic maintenance (pump, autosampler) and Hardware problems. Under QCWI 001 §6, repairs are done only by the manufacturer\'s authorised service; '
       'analysts may do the daily items (filters, rinse solution, purge) and must record every part change in QCLB 018.'),
 ('h', '11.4 After the analysis'),
 ('steps', [
   ('Stop pump delivery and oven heating.', 'GS_54_1'),
   ('Switch the instrument off in the software; select [Exit] when the oven has cooled; save any unsaved method.', 'GS_55_0'),
   ('Exit LabSolutions, shut down Windows, switch the PC and the instruments off.', None),
 ], GS + ', pp. 54–55'),
 ('box', 'tip', 'Column and flow-path care',
  'If the system will stand unused: rinse the column, remove and store it as its instruction sheet says; replace the column with a union and rinse the flow path; '
  'leave it in an alcohol (2-propanol or methanol) so nothing grows in it (' + OPG + ', p. 36). Automatic shutdown with a cool-down time can be set in the batch (Module 6).'),
])

# ---------------------------------------------------------------------------
module(12, 'Troubleshooting, with our 30.10.2026 failure as the case study',
 'Go from a symptom to its probable cause with Shimadzu\'s own tables, and reason through a real failure from our laboratory.',
[
 ('h', '12.1 Pump, pressure and flow'),
 ('table', ['Symptom', 'Check', 'Remedy'], [
   ['Pressure does not rise', 'Drain valve open? Leak at a connection?', 'Close it. Retighten; replace the fitting if it still leaks.'],
   ['Instrument runs but does not pump', 'Bottle empty? Drain valve open? Check valve? Air at suction-filter fitting? Bubbles in pump head?', 'Refill; close; rinse/sonicate/replace check valve; tighten; purge or draw air out with a syringe at the drain tube.'],
   ['Unstable pumping / flow lower than set', 'Suction or line filter clogged; bubbles in suction tube; old mobile phase in head; seal leak', 'Sonicate/replace filters; purge, tap the filter, degas; purge thoroughly; replace seal (and plunger).'],
   ['Pressure too high', 'Line filter, tubing bore, column clogged', 'Sonicate/replace filter; correct tubing; replace column.'],
 ]),
 ('p', 'Source: ' + VA + ', Troubleshooting hardware problems.'),
 ('h', '12.2 Chromatogram'),
 ('table', ['Symptom', 'Probable causes'], [
   ['Retention times change', 'Flow; insufficient equilibration (≥ 10 column volumes); oven temperature; wrong mobile phase or proportioning; leaks; air in pump; worn needle seal.'],
   ['Baseline drift', 'Column temperature; low-quality or poorly degassed mobile phase; contamination or bubble in the cell; poor mixing; slow equilibration; strongly retained material eluting later; lamp warm-up < 1 h.'],
   ['Noise', 'Air in cell or pump; leak; incomplete mixing; temperature at the detector; contaminated mobile phase; old lamp (> 2,000 h).'],
   ['Cyclic waviness', 'Air conditioning blowing on the detector or large room-temperature swings.'],
   ['Ghost peaks', 'Mobile phase purity; dirty rinse port, needle or loop; old solvent left in lines.'],
 ]),
 ('p', 'Sources: ' + TS + ', pp. 14, 17, 22; ' + VA + ', Chromatogram problems; ' + OPG + ', p. 36.'),
 ('h', '12.3 Case study: 30.10.2026'),
 ('p', '<b>What happened.</b> Fresh/moist flower samples (MAC, ZCAP, DD, SHM) were run with method <code>HighThroughput_PDAcal 31102025_novi RT 1103.lcm</code>. '
       'The results were unusable. The air conditioning had been adjusted that day (room 20–24 °C). Work through the evidence below before reading the conclusions.'),
 ('figrow', [
   ('PHOTO:3.jpg', 'A. Reference: standard STD_005, 15.09.2026. Flat baseline; CBDA 2.838, CBD 3.228, CBN 4.155, d9-THC 4.859, d8-THC 4.983, THCA 5.802 min.'),
   ('PHOTO:2.jpg', 'B. Same standard, 30.10.2026. CBDA 2.825 and CBD 3.223 "found"; d9-THC, d8-THC, THCA not found; three unnamed peaks; dip at ~5 min; Sample Type: Unknown.'),
   ('PHOTO:4.jpg', 'C. System blank, 30.10.2026, vial −1 (no injection): ~50 mAU excursion and a "CBN" peak at 4.129 min with nothing injected.'),
 ]),
 ('fig', 'PHOTO:c90319cd-image.jpg', 'Data Acquisition on 30.10.2026: low-pressure gradient, lines C/D unassigned, pressure 42 bar.', 70),
 ('table', ['Evidence', 'What it tells you'], [
   ['The no-injection blank is disturbed', 'The fault is in mobile phase, pump, column or detector, not in samples or standards.'],
   ['The dip is at the same time in the blank and in the standard', 'It is locked to the run: a composition/flow event, not the room temperature (which does not follow the injection).'],
   ['Early acids barely moved, late compounds vanished', 'Elution strength changed (composition), not temperature (which moves all peaks one way).'],
   ['Negative spectrum below 250 nm', 'The composition reaching the detector changed after zeroing.'],
   ['Pressure 42–43 bar that does not rise with flow', 'The pump is not delivering the set flow/composition: drain valve, leak, air in line A or in the proportioning valve, check valve.'],
   ['Oven 44.9 / 50 °C and flow 1.0 mL/min during a run', 'The run started before the system was at method conditions; the flow was set by hand.'],
   ['Standards entered as Unknown', 'No calibration from the day\'s standards.'],
 ]),
 ('box', 'gmp', 'Lessons',
  '<ol><li>Do not accept a convenient external cause (the air conditioning) without evidence; test it with the Room Temp. curve.</li>'
  '<li>Prove the pump before injecting: pressure must follow flow (Module 4.4).</li>'
  '<li>Fill and purge all four lines of a low-pressure gradient pump.</li>'
  '<li>Never acquire while ramping or before [Ready].</li>'
  '<li>Standards are Standard (I)/Standard, never Unknown.</li>'
  '<li>Investigate as a laboratory deviation; results are not reported until the root cause is shown (EU GMP Part I 6.7(iv), 6.35; ICH Q9(R1)).</li></ol>'),
])
