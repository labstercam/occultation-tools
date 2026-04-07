"use strict";
// build-ntp-presentation.js
// Run from presentations/ folder:  node build-ntp-presentation.js

const PptxGenJS = require("pptxgenjs");

// ── Palette ──────────────────────────────────────────────────────────────────
const BG       = "0d1b2a";
const TEXT     = "d6e4f0";
const ACCENT   = "5bc0eb";
const H2C      = "8bb8d0";
const PANEL_BG = "1a3a5a";
const ALT_ROW  = "0f1e2a";
const BORDER   = "1e3040";
const STRONG   = "7ed6f5";
const WARN     = "e87070";
const MUTED    = "5a7a9a";
const QUOTE_BG = "0a2233";

// ── Typography ───────────────────────────────────────────────────────────────
const FT = "Trebuchet MS";   // title font
const FB = "Calibri";        // body font

const ASSETS = "./assets/";

// ── Presentation setup ───────────────────────────────────────────────────────
const pres = new PptxGenJS();
pres.layout  = "LAYOUT_16x9";   // 10" × 5.625"
pres.title   = "NTP Timing for Occultations";
pres.subject = "Practical NTP timing for asteroid occultation observers";
pres.author  = "labstercam";

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Dark-background slide with left accent bar */
function contentSlide() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addShape(pres.ShapeType.rect, {
    x: 0.22, y: 0.18, w: 0.05, h: 5.0,
    fill: { color: ACCENT },
    line: { color: ACCENT }
  });
  return s;
}

/** Plain dark slide — no bar */
function plainSlide() {
  const s = pres.addSlide();
  s.background = { color: BG };
  return s;
}

function addTitle(s, text, y = 0.18) {
  s.addText(text, {
    x: 0.42, y, w: 9.1, h: 0.62,
    fontFace: FT, fontSize: 30, bold: true, color: ACCENT,
    valign: "middle", margin: 0
  });
}

function addSubtitle(s, text, y = 0.86) {
  s.addText(text, {
    x: 0.42, y, w: 9.1, h: 0.32,
    fontFace: FB, fontSize: 17, color: H2C,
    valign: "top", margin: 0
  });
}

/** Add a bordered callout panel */
function addCallout(s, text, x, y, w, h, textOpts) {
  s.addShape(pres.ShapeType.rect, {
    x, y, w, h,
    fill: { color: PANEL_BG },
    line: { color: ACCENT, pt: 1 }
  });
  s.addText(text, Object.assign({
    x: x + 0.15, y: y + 0.04, w: w - 0.3, h: h - 0.08,
    fontFace: FB, fontSize: 14, color: ACCENT, bold: true,
    valign: "middle", margin: 0
  }, textOpts || {}));
}

/** Table cell helpers — each call returns a fresh object */
const hCell = (text) => ({ text, options: { bold: true, color: ACCENT, fill: { color: PANEL_BG } } });
const hCellW = (text) => ({ text, options: { bold: true, color: ACCENT, fill: { color: PANEL_BG }, align: "left" } });
const dCell = (text, extra) => ({ text, options: Object.assign({ fill: { color: BG } },      extra || {}) });
const aCell = (text, extra) => ({ text, options: Object.assign({ fill: { color: ALT_ROW } }, extra || {}) });
const bCell = (text, c)     => ({ text, options: { bold: true, color: c || STRONG, fill: { color: BG } } });
const baCell = (text, c)    => ({ text, options: { bold: true, color: c || STRONG, fill: { color: ALT_ROW } } });

const TABLE_DEFAULTS = {
  fontFace: FB, fontSize: 14,
  border: { pt: 1, color: BORDER },
  fill: { color: BG },
  autoPage: false,
  align: "left", valign: "middle",
  color: TEXT
};

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — Hook
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { path: ASSETS + "occultation-map.png" };

  // Dark overlay
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: "000000", transparency: 42 },
    line: { color: "000000" }
  });

  s.addText("No observations.", {
    x: 0.8, y: 1.5, w: 8.4, h: 0.9,
    fontFace: FT, fontSize: 52, bold: true, color: "FFFFFF",
    align: "left", valign: "middle"
  });
  s.addText("Not because no one had a camera.", {
    x: 0.8, y: 2.62, w: 8.4, h: 0.6,
    fontFace: FB, fontSize: 24, color: TEXT,
    align: "left", valign: "middle"
  });
  s.addText("Because no one thought they could time it.", {
    x: 0.8, y: 3.32, w: 8.4, h: 0.6,
    fontFace: FB, fontSize: 24, bold: true, color: ACCENT,
    align: "left", valign: "middle"
  });
  s.addText("NTP Timing for Occultations  \u2014  April 2026", {
    x: 0.8, y: 4.95, w: 8.4, h: 0.35,
    fontFace: FB, fontSize: 13, color: MUTED,
    align: "left"
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — The assumed path
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "The assumed path");
  addSubtitle(s, "Most people researching occultation timing find this:");

  s.addText([
    { text: "1.  ",                       options: { color: H2C } },
    { text: "\u201CYou need a GPS timing device\u2026\u201D", options: { color: TEXT, breakLine: true } },
    { text: "2.  ",                       options: { color: H2C } },
    { text: "\u201COr an analog camera and VTI\u2026\u201D",  options: { color: TEXT, breakLine: true } },
    { text: "3.  ",                       options: { color: H2C } },
    { text: "\u201COr a dedicated camera\u2026\u201D",        options: { color: TEXT, breakLine: true } },
    { text: "4.  Hardware cost: ",        options: { color: TEXT } },
    { text: "$500 \u2013 $1,200+ US",     options: { bold: true, color: STRONG, breakLine: true } },
    { text: "5.  ",                       options: { color: H2C } },
    { text: "\u2192 They close the tab.", options: { bold: true, color: WARN } },
  ], {
    x: 0.55, y: 1.22, w: 8.9, h: 2.7,
    fontFace: FB, fontSize: 18, color: TEXT,
    valign: "top", paraSpaceAfter: 6
  });

  addCallout(s, "There is a Step 0 they were never told about.", 0.42, 4.22, 9.1, 0.78);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — What NTP actually delivers
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "What NTP actually delivers");
  addSubtitle(s, "Home observatory PC \u2014 domestic fibre");

  s.addImage({
    path: ASSETS + "ntp-server-monitor-status.png",
    x: 0.42, y: 1.22,
    sizing: { type: "contain", w: 9.1, h: 2.62 }
  });

  s.addText([
    { text: "Offset: \u22120.035\u202Fms",     options: { bold: true, color: STRONG } },
    { text: " \u2014 that is 35 ",              options: {} },
    { text: "microseconds",                     options: { italic: true } },
    { text: ", not milliseconds.  All active servers GPS-referenced at Stratum\u00A01.  Reach\u00A0377 \u2014 every poll responded.", options: { breakLine: true } },
    { text: "The \u201C\u00B1100\u202Fms\u201D fear = Windows default time service, ", options: {} },
    { text: "not",                              options: { bold: true, color: WARN, italic: true } },
    { text: " configured NTP.",                options: {} },
  ], {
    x: 0.42, y: 3.9, w: 9.1, h: 1.3,
    fontFace: FB, fontSize: 13.5, color: TEXT,
    valign: "top", paraSpaceAfter: 4
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — Is 5 ms good enough?
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "Is 5\u202Fms good enough?");
  addSubtitle(s, "For a typical main-belt occultation, mag\u00A012\u201313, 100\u202Fms exposure:");

  const rows4 = [
    [ hCell("Source"),                                          hCell("Uncertainty") ],
    [ dCell("NTP clock (PIT estimate from logs)"),              dCell("~5 ms")       ],
    [ aCell("Camera line delay (measured)"),                    aCell("~1 ms")       ],
    [ dCell("Camera frame delay (estimated)"),                  dCell("~2 ms")       ],
    [ baCell("Total (RSS)"),                                    baCell("~6 ms")      ],
  ];
  s.addTable(rows4, Object.assign({}, TABLE_DEFAULTS, {
    x: 0.42, y: 1.22, w: 9.1, h: 2.0,
    colW: [6.6, 2.5], rowH: 0.36
  }));

  // Quote box
  s.addShape(pres.ShapeType.rect, {
    x: 0.42, y: 3.35, w: 9.1, h: 1.9,
    fill: { color: QUOTE_BG },
    line: { color: ACCENT, pt: 1 }
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.42, y: 3.35, w: 0.06, h: 1.9,
    fill: { color: ACCENT },
    line: { color: ACCENT }
  });
  s.addText([
    { text: "\u201CAbout 5\u202Fms is accurate enough for most observing situations.\n", options: { italic: true } },
    { text: "Reliability and traceability are more important than the raw accuracy number.\u201D\n", options: { italic: true, breakLine: true } },
    { text: "\u2014 Dave Herald",       options: { bold: true, color: STRONG, italic: false } },
    { text: ", IOTA worldwide coordinator", options: { color: H2C } },
  ], {
    x: 0.62, y: 3.42, w: 8.8, h: 1.76,
    fontFace: FB, fontSize: 13.5, color: "b8d8f0",
    valign: "top", paraSpaceAfter: 6
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — You can verify it — exactly
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "You can verify it \u2014 exactly");
  addSubtitle(s, "NTP Clock Accuracy in Occultation Manager");

  s.addText([
    { text: "Event: 2004\u202FDG41 \u2014 2026-03-02 10:58\u202FUTC\n", options: { bold: true, color: STRONG, breakLine: true } },
    { text: "\n", options: { fontSize: 5, breakLine: true } },
    { text: "Offset: ",    options: {} },
    { text: "\u22120.380\u202Fms\n", options: { bold: true, color: STRONG, breakLine: true } },
    { text: "Uncertainty: ", options: {} },
    { text: "\u00B14.879\u202Fms (95%)\n", options: { bold: true, color: STRONG, breakLine: true } },
    { text: "Data age: 0\u202Fmin before event\n", options: { breakLine: true } },
    { text: "\n", options: { fontSize: 5, breakLine: true } },
    { text: "\u201CMy clock was \u22120.38\u202Fms off at disappearance.\u201D\n", options: { italic: true, color: "b8d8f0", breakLine: true } },
    { text: "\n", options: { fontSize: 5, breakLine: true } },
    { text: "That number goes directly into the observation report.\n", options: { breakLine: true } },
    { text: "Most GPS-camera users never document this at all.", options: { color: H2C } },
  ], {
    x: 0.42, y: 1.22, w: 4.5, h: 4.1,
    fontFace: FB, fontSize: 13.5, color: TEXT,
    valign: "top", paraSpaceAfter: 4
  });

  s.addImage({
    path: ASSETS + "ntp-accuracy-example1.png",
    x: 5.08, y: 0.88,
    sizing: { type: "contain", w: 4.67, h: 4.45 }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — GPS ground-truth verification
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "GPS ground-truth verification");
  addSubtitle(s, "GPS vs NTP Testing \u2014 23 hours against GPS PPS reference");

  s.addText([
    { text: "Mean UTC error: ", options: {} },
    { text: "0.097\u202Fms\n",   options: { bold: true, color: STRONG, breakLine: true } },
    { text: "U(k=2): ",           options: {} },
    { text: "\u00B19.4\u202Fms\n", options: { bold: true, color: STRONG, breakLine: true } },
    { text: "Best servers: ",     options: {} },
    { text: "\u00B10.5\u20131\u202Fms", options: { bold: true, color: STRONG } },
    { text: " of GPS\n",          options: { breakLine: true } },
    { text: "\n",                 options: { fontSize: 5, breakLine: true } },
    { text: "The calibration chain:\n", options: { bold: true, color: H2C, breakLine: true } },
    { text: "UTC \u2190 GPS PPS \u2190 NTP servers \u2190 your clock", options: { color: ACCENT, bold: true } },
  ], {
    x: 0.42, y: 1.22, w: 3.2, h: 4.1,
    fontFace: FB, fontSize: 14, color: TEXT,
    valign: "top", paraSpaceAfter: 6
  });

  s.addImage({
    path: ASSETS + "gps-pps-comparison.png",
    x: 3.75, y: 0.9,
    sizing: { type: "contain", w: 5.98, h: 4.42 }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — 10-minute install. Free.
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = plainSlide();

  // Horizontal rule top
  s.addShape(pres.ShapeType.rect, {
    x: 3.0, y: 1.18, w: 4.0, h: 0.04,
    fill: { color: ACCENT }, line: { color: ACCENT }
  });

  s.addText("10-minute install.", {
    x: 0.5, y: 1.3, w: 9, h: 1.1,
    fontFace: FT, fontSize: 54, bold: true, color: ACCENT,
    align: "center", valign: "middle"
  });
  s.addText("Free.", {
    x: 0.5, y: 2.4, w: 9, h: 1.05,
    fontFace: FT, fontSize: 54, bold: true, color: ACCENT,
    align: "center", valign: "middle"
  });
  s.addText("Everything configured automatically.", {
    x: 0.5, y: 3.62, w: 9, h: 0.6,
    fontFace: FB, fontSize: 22, italic: true, color: TEXT,
    align: "center", valign: "middle"
  });

  // Horizontal rule bottom
  s.addShape(pres.ShapeType.rect, {
    x: 3.0, y: 4.35, w: 4.0, h: 0.04,
    fill: { color: ACCENT }, line: { color: ACCENT }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — The NTP Installer
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "The NTP Installer");

  s.addText("One run configures everything:", {
    x: 0.42, y: 0.9, w: 4.5, h: 0.4,
    fontFace: FB, fontSize: 15, bold: true, color: STRONG
  });

  s.addText([
    { text: "Meinberg NTP + Time Server Monitor",             options: { bullet: true, breakLine: true } },
    { text: "National standards servers for 35 countries",   options: { bullet: true, breakLine: true } },
    { text: "Windows network QoS optimisation (DSCP\u00A046)", options: { bullet: true, breakLine: true } },
    { text: "Optional GPS PPS receiver setup",               options: { bullet: true } },
  ], {
    x: 0.42, y: 1.35, w: 4.5, h: 1.75,
    fontFace: FB, fontSize: 14, color: TEXT,
    valign: "top", paraSpaceAfter: 5
  });

  s.addText("Estimated time: 10\u201320\u202Fminutes", {
    x: 0.42, y: 3.18, w: 4.5, h: 0.4,
    fontFace: FB, fontSize: 14, bold: true, color: STRONG
  });
  s.addText("\u201CYou can set this up in the time it takes to make a toasted cheese sandwich.\u201D", {
    x: 0.42, y: 3.65, w: 4.5, h: 0.68,
    fontFace: FB, fontSize: 12.5, italic: true, color: "b8d8f0"
  });
  s.addText("github.com/labstercam/occultation-ntp-installer", {
    x: 0.42, y: 4.42, w: 4.5, h: 0.38,
    fontFace: FB, fontSize: 12, color: ACCENT
  });

  s.addImage({
    path: ASSETS + "NTP-Installer.png",
    x: 5.1, y: 0.88,
    sizing: { type: "contain", w: 4.65, h: 4.45 }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — Camera delays — estimated without a flasher
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "Camera delays \u2014 estimated without a flasher");

  addCallout(s,
    "per_line_delay = (1 / max_fps) / ROI_height \u00D7 1000\u202Fms    \u2014    Occultation Manager calculates this automatically",
    0.42, 0.88, 9.1, 0.52, { fontSize: 12.5 }
  );

  s.addImage({
    path: ASSETS + "camera-coefs.png",
    x: 0.42, y: 1.48,
    sizing: { type: "contain", w: 9.1, h: 1.8 }
  });

  s.addText("ZWO ASI462MM, 408\u00D7411 ROI, binning \u00D72 \u2014 Per-line: \u22120.0287\u202Fms | Frame delay (Line\u00A00): 13.8\u202Fms", {
    x: 0.42, y: 3.35, w: 9.1, h: 0.38,
    fontFace: FB, fontSize: 12.5, color: H2C, italic: true
  });

  s.addText([
    { text: "Frame delay for small sensors, small ROI: typically ", options: { breakLine: false } },
    { text: "< 2\u202Fms",  options: { bold: true, color: STRONG, breakLine: true } },
    { text: "Use community-shared calibrations for your camera", options: { bullet: true, breakLine: true } },
    { text: "Not suitable: USB\u00A02.0 cameras; sensors \u22654/3\u2033 with full-frame ROI", options: { bullet: true, color: WARN } },
  ], {
    x: 0.42, y: 3.8, w: 9.1, h: 1.4,
    fontFace: FB, fontSize: 13.5, color: TEXT,
    valign: "top", paraSpaceAfter: 5
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — Camera delays — measured with a flasher
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "Camera delays \u2014 measured with a flasher");
  addSubtitle(s, "A $10 GPS receiver is all you need");

  s.addText("HiLetgo VK172, Beitian BN-180, or similar", {
    x: 0.42, y: 1.22, w: 4.6, h: 0.36,
    fontFace: FB, fontSize: 13, italic: true, color: H2C
  });
  s.addText("Camera Timing Setup \u2014 Line Delay Calibration", {
    x: 0.42, y: 1.62, w: 4.6, h: 0.4,
    fontFace: FB, fontSize: 14, bold: true, color: STRONG
  });
  s.addText("Result: \u201CLine delay: 12.8 \u2212 0.028 \u00D7 Y ms\u201D", {
    x: 0.42, y: 2.08, w: 4.6, h: 0.4,
    fontFace: FB, fontSize: 13.5, color: TEXT
  });
  s.addText([
    { text: "R\u00B2\u00A0=\u00A00.990", options: { bold: true, color: STRONG } },
    { text: " \u2014 Excellent",          options: {} },
  ], {
    x: 0.42, y: 2.52, w: 4.6, h: 0.4,
    fontFace: FB, fontSize: 14, color: TEXT
  });
  s.addText("Clean linear fit across the full sensor height.\nEven a cheap receiver produces sub-millisecond calibration precision.", {
    x: 0.42, y: 3.0, w: 4.6, h: 0.9,
    fontFace: FB, fontSize: 13, color: H2C, italic: true
  });

  s.addImage({
    path: ASSETS + "gps-camera-calibration.png",
    x: 5.08, y: 0.88,
    sizing: { type: "contain", w: 4.67, h: 4.45 }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 11 — Camera delay is stable
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "Camera delay is stable");
  addSubtitle(s, "27,042 GPS flashes \u2014 9 continuous hours");

  const rows11 = [
    [ hCell("Stat"),          hCell("Value")                                              ],
    [ dCell("Mean"),          bCell("7.377\u202Fms")                                      ],
    [ aCell("95% CI"),        baCell("\u00B1\u00A00.006\u202Fms")                         ],
    [ dCell("Std Dev"),       dCell("0.465\u202Fms")                                      ],
    [ aCell("Range"),         aCell("6.2 \u2013 8.5\u202Fms")                             ],
  ];
  s.addTable(rows11, Object.assign({}, TABLE_DEFAULTS, {
    x: 0.42, y: 1.22, w: 4.4, h: 2.2,
    colW: [2.4, 2.0], rowH: 0.4
  }));

  s.addText("\u201CHow do you know the camera delay doesn\u2019t drift?\u201D", {
    x: 0.42, y: 3.56, w: 4.4, h: 0.52,
    fontFace: FB, fontSize: 13.5, italic: true, color: "b8d8f0"
  });
  s.addText("27,000 measurements over 9 hours say: it doesn\u2019t.", {
    x: 0.42, y: 4.12, w: 4.4, h: 0.52,
    fontFace: FB, fontSize: 14, bold: true, color: STRONG
  });
  s.addText("Measure once per camera/ROI/settings combination. Use with confidence.", {
    x: 0.42, y: 4.68, w: 4.4, h: 0.42,
    fontFace: FB, fontSize: 12.5, color: H2C
  });

  s.addImage({
    path: ASSETS + "gps-stability-test.png",
    x: 4.96, y: 0.88,
    sizing: { type: "contain", w: 4.79, h: 4.45 }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 12 — What it costs
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "What it costs");

  const rows12 = [
    [ hCell("Component"),                                                  hCell("What"),                            hCell("Cost")             ],
    [ dCell("Windows PC"),                                                 dCell("Already own"),                     dCell("$0")               ],
    [ aCell("USB3 camera"),                                                aCell("Already own / ToupTek G3M662M"),   aCell("$0 or ~$US\u202F179") ],
    [ dCell("SharpCap Pro"),                                               dCell("Capture software"),                dCell("~$US\u202F20/yr")  ],
    [ aCell("Meinberg NTP"),                                               aCell("Clock discipline"),                aCell("Free")             ],
    [ dCell("NTP Installer"),                                              dCell("All-in-one setup"),                dCell("Free")             ],
    [ aCell("Occultation Manager"),                                        aCell("Events, sequences, reports"),      aCell("Free")             ],
    [ bCell("Total new cost"), dCell(""),                                  bCell("~$US\u202F20")                    ],
  ];
  s.addTable(rows12, Object.assign({}, TABLE_DEFAULTS, {
    x: 0.42, y: 0.95, w: 9.1, h: 2.9,
    colW: [2.55, 4.5, 2.05], rowH: 0.34
  }));

  s.addText("Optional upgrades:", {
    x: 0.42, y: 3.95, w: 9.1, h: 0.34,
    fontFace: FB, fontSize: 14, bold: true, color: H2C
  });

  const rows12b = [
    [ hCell("Item"),                         hCell("Via"),                                  hCell("Approx."),              hCell("Benefit")                       ],
    [ dCell("GPS PPS receiver + flasher"),   dCell("DIY"),                                  bCell("~$50\u201380\u202FAUD"), dCell("Sub-ms clock + measured delays") ],
    [ aCell("Dedicated flash timer"),        aCell("Aarts Timers, StampOfApproval"),        baCell("~$80\u2013200\u202FAUD"), aCell("Most versatile")              ],
  ];
  s.addTable(rows12b, Object.assign({}, TABLE_DEFAULTS, {
    x: 0.42, y: 4.34, w: 9.1, h: 0.98,
    colW: [2.4, 2.55, 1.7, 2.45], rowH: 0.4, fontSize: 12.5
  }));
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 13 — The upgrade path
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "The upgrade path");
  addSubtitle(s, "Start today. Upgrade when you\u2019re ready.");

  const rows13 = [
    [ hCell("Level"),             hCell("Clock"),       hCell("Camera delays"),        hCell("Typical cost")  ],
    [ bCell("0 \u2014 NTP only"), dCell("~5\u202Fms"),  dCell("Estimated from max FPS"), bCell("~$20")        ],
    [ aCell("1 \u2014 + GPS PPS + flasher"), aCell("< 1\u202Fms"), aCell("Measured \u00B1 1\u202Fms"), aCell("+ $50\u2013120") ],
    [ dCell("2 \u2014 TimeBox / GPS NTP server"), dCell("< 1\u202Fms"), dCell("Measured \u00B1 1\u202Fms"), dCell("+ $150\u2013250") ],
    [ aCell("3 \u2014 Dedicated camera"), aCell("Built-in GPS"), aCell("Built-in"), aCell("$700\u20131,200+") ],
  ];
  s.addTable(rows13, Object.assign({}, TABLE_DEFAULTS, {
    x: 0.42, y: 1.22, w: 9.1, h: 2.15,
    colW: [2.6, 1.5, 2.7, 2.3], rowH: 0.41
  }));

  s.addText([
    { text: "Level 0 covers the ",        options: {} },
    { text: "majority of events.",        options: { bold: true, color: STRONG } },
    { text: "  Level 3 is the ",          options: {} },
    { text: "destination",               options: { italic: true, color: STRONG } },
    { text: ", not the entry requirement.", options: {} },
  ], {
    x: 0.42, y: 3.5, w: 9.1, h: 0.45,
    fontFace: FB, fontSize: 14, color: TEXT, valign: "middle"
  });

  // Quote box
  s.addShape(pres.ShapeType.rect, {
    x: 0.42, y: 4.05, w: 9.1, h: 1.22,
    fill: { color: QUOTE_BG },
    line: { color: ACCENT, pt: 1 }
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.42, y: 4.05, w: 0.06, h: 1.22,
    fill: { color: ACCENT },
    line: { color: ACCENT }
  });
  s.addText("\u201CStart at Level\u00A00 today and learn how to do occultations. Upgrade later when you need to.\u201D", {
    x: 0.62, y: 4.1, w: 8.8, h: 1.12,
    fontFace: FB, fontSize: 13.5, italic: true, color: "b8d8f0",
    valign: "middle"
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 14 — Start tonight
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = contentSlide();
  addTitle(s, "Start tonight");

  // Three audience columns
  const cols = [
    {
      header: "New observers",
      body:   "Download and run the installer. Check NTP status in the morning.\nIf the numbers look good \u2014 you can do occultations."
    },
    {
      header: "Experienced observers & clubs",
      body:   "NTP is free, works, and accuracy is verifiable and traceable to UTC.\nHelp your members start \u2014 every new observer adds chords to every campaign."
    },
    {
      header: "Campaign coordinators",
      body:   "NTP observers expand multi-station coverage at zero hardware cost.\nLet\u2019s get this listed formally."
    }
  ];

  const colW = 2.85;
  const gutter = 0.245;
  const x0 = 0.42;
  const headerH = 0.58;
  const bodyY = 1.22 + headerH + 0.08;

  cols.forEach((col, i) => {
    const cx = x0 + i * (colW + gutter);

    // Header panel
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: 1.22, w: colW, h: headerH,
      fill: { color: PANEL_BG },
      line: { color: ACCENT, pt: 1 }
    });
    s.addText(col.header, {
      x: cx + 0.1, y: 1.22, w: colW - 0.2, h: headerH,
      fontFace: FB, fontSize: 14, bold: true, color: ACCENT,
      valign: "middle", align: "left", margin: 0
    });

    // Body text
    s.addText(col.body, {
      x: cx, y: bodyY, w: colW, h: 3.3,
      fontFace: FB, fontSize: 13.5, color: TEXT,
      valign: "top", paraSpaceAfter: 8
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 15 — Links
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = plainSlide();

  // Subtle map background
  s.background = { path: ASSETS + "occultation-map.png" };
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: "000000", transparency: 68 },
    line: { color: "000000" }
  });

  s.addText("Links", {
    x: 0.5, y: 0.55, w: 9, h: 0.7,
    fontFace: FT, fontSize: 36, bold: true, color: ACCENT,
    align: "center"
  });

  s.addShape(pres.ShapeType.rect, {
    x: 3.0, y: 1.38, w: 4.0, h: 0.04,
    fill: { color: ACCENT }, line: { color: ACCENT }
  });

  const links = [
    { label: "NTP Installer",  url: "github.com/labstercam/occultation-ntp-installer" },
    { label: "Tools & docs",   url: "github.com/labstercam/occultation-tools" },
  ];

  links.forEach((lnk, i) => {
    const y = 1.65 + i * 0.95;
    s.addText(lnk.label, {
      x: 0.5, y, w: 9, h: 0.38,
      fontFace: FB, fontSize: 16, bold: true, color: H2C,
      align: "center"
    });
    s.addText(lnk.url, {
      x: 0.5, y: y + 0.4, w: 9, h: 0.45,
      fontFace: FB, fontSize: 18, color: ACCENT,
      align: "center"
    });
  });

  s.addText("NTP Timing for Occultations  \u2014  April 2026", {
    x: 0.5, y: 5.05, w: 9, h: 0.35,
    fontFace: FB, fontSize: 13, color: MUTED,
    align: "center"
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// Write output
// ═══════════════════════════════════════════════════════════════════════════════
pres.writeFile({ fileName: "ntp-timing-for-occultations.pptx" })
  .then(() => console.log("Done: ntp-timing-for-occultations.pptx"))
  .catch(err => { console.error("Error:", err); process.exit(1); });
