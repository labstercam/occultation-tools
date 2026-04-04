---
applyTo: "**/*.pptx,**/presentations/**,**/*.marp.md"
---

# PPTX / Presentation Skill

Use this guidance any time a `.pptx` file is involved — creating, reading, editing, or
converting — and when working with Marp `.marp.md` presentation files.

---

## Quick Reference

| Task | Approach |
|------|----------|
| Read/analyse content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Follow the Template-Based Workflow below |
| Create from scratch | Follow the PptxGenJS Workflow below |
| Visual QA | Convert to images, inspect each slide |

---

## Reading Content

```powershell
# Text extraction (install once: pip install "markitdown[pptx]")
python -m markitdown presentation.pptx

# Unpack for raw XML inspection
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Template-Based Editing Workflow

1. **Analyse existing slides**
   ```powershell
   python -m markitdown template.pptx
   ```
   Review content, choose layouts. Actively seek varied layouts — monotonous
   presentations are the most common failure mode. Look for:
   - Multi-column layouts (2-column, 3-column)
   - Image + text combinations
   - Full-bleed images with text overlay
   - Quote or callout slides
   - Section dividers, stat/number callouts, icon grids

2. **Unpack**
   ```powershell
   python scripts/office/unpack.py template.pptx unpacked/
   ```

3. **Structural changes first** (before editing content):
   - Delete unwanted slides — remove from `<p:sldIdLst>` in `ppt/presentation.xml`
   - Duplicate slides — use `add_slide.py` (never manually copy slide files)
   - Reorder `<p:sldId>` elements as needed
   - Complete ALL structural changes before editing text

4. **Edit content** — update text in each `slide{N}.xml`
   - Use the Edit tool, not sed or Python scripts (forces precision)
   - Bold all headers, subheaders, and inline labels: `b="1"` on `<a:rPr>`
   - Never use unicode bullets (•) — use `<a:buChar>` or `<a:buAutoNum>`
   - Separate list items into separate `<a:p>` elements — never concatenate into one string
   - For quotes in XML use entities: `&#x201C;` `&#x201D;` `&#x2018;` `&#x2019;`
   - Use `xml:space="preserve"` on `<a:t>` with leading/trailing spaces
   - Use `defusedxml.minidom` for XML parsing — never `xml.etree.ElementTree` (corrupts namespaces)

5. **Clean**
   ```powershell
   python scripts/clean.py unpacked/
   ```

6. **Pack**
   ```powershell
   python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
   ```

---

## Creating from Scratch with PptxGenJS

Install once:
```powershell
npm install -g pptxgenjs
npm install -g react-icons react react-dom sharp   # for icons
pip install Pillow                                  # for thumbnails
```

### Basic Structure

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';   // 10" × 5.625"
pres.title = 'Presentation Title';

let slide = pres.addSlide();
slide.addText("Hello World!", { x: 0.5, y: 0.5, fontSize: 36, color: "363636" });

pres.writeFile({ fileName: "output.pptx" });
```

### Layout Dimensions

| Layout | Dimensions |
|--------|-----------|
| `LAYOUT_16x9` (default) | 10" × 5.625" |
| `LAYOUT_16x10` | 10" × 6.25" |
| `LAYOUT_4x3` | 10" × 7.5" |
| `LAYOUT_WIDE` | 13.3" × 7.5" |

### Text

```javascript
// Basic text box
slide.addText("Title", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, fontFace: "Georgia", color: "1E2761", bold: true,
  margin: 0  // set to 0 when aligning with shapes/icons at same x
});

// Rich text (multi-run)
slide.addText([
  { text: "Bold ", options: { bold: true } },
  { text: "Normal", options: { bold: false } }
], { x: 1, y: 1, w: 8, h: 1 });

// Multi-line (use breakLine: true)
slide.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2", options: { breakLine: true } },
  { text: "Line 3" }
], { x: 0.5, y: 0.5, w: 8, h: 2 });

// Character spacing
slide.addText("HEADER", { x: 1, y: 1, w: 8, h: 1, charSpacing: 6 });
```

### Lists / Bullets

```javascript
// ✅ CORRECT
slide.addText([
  { text: "First item", options: { bullet: true, breakLine: true } },
  { text: "Second item", options: { bullet: true, breakLine: true } },
  { text: "Third item", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });

// ❌ WRONG — never use unicode "•" — creates double bullets
```

### Shapes

```javascript
// Rectangle (use for accent bars — NOT ROUNDED_RECTANGLE with accents)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 0.08, h: 3.0,
  fill: { color: "028090" }
});

// Shadow — create fresh object per call (PptxGenJS mutates in-place)
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" }, shadow: makeShadow()
});
```

### Images

```javascript
slide.addImage({ path: "images/chart.png", x: 1, y: 1, w: 5, h: 3 });
// Contain (preserve ratio)
slide.addImage({ path: "image.png", x: 1, y: 1, sizing: { type: 'contain', w: 4, h: 3 } });
// Calculate width to preserve aspect ratio
const calcWidth = 3.0 * (origWidth / origHeight);
```

### Icons (react-icons → PNG)

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaCheckCircle } = require("react-icons/fa");

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

const iconData = await iconToBase64Png(FaCheckCircle, "#028090", 256);
slide.addImage({ data: iconData, x: 1, y: 1, w: 0.4, h: 0.4 });
```

Use size ≥ 256 for crisp rendering. Display size is controlled by `w`/`h` in inches.

### Charts (modern styling)

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",
  chartColors: ["028090", "00A896", "02C39A"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  catAxisLabelColor: "64748B", valAxisLabelColor: "64748B",
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: "1E293B",
  showLegend: false
});
```

---

## PptxGenJS Common Pitfalls

1. **NEVER use `#` with hex colors** — `color: "FF0000"` ✅  `color: "#FF0000"` ❌ (corrupts file)
2. **NEVER encode opacity in hex** — 8-char colors like `"00000020"` corrupt the file. Use `opacity: 0.12` instead
3. **NEVER reuse option objects** across calls — PptxGenJS mutates them in-place; use a factory function
4. **NEVER use unicode `•`** for bullets — use `bullet: true`
5. **Use `breakLine: true`** between array items
6. **Avoid `lineSpacing` with bullets** — use `paraSpaceAfter` instead
7. **Don't use `ROUNDED_RECTANGLE` with rectangular accent overlays** — corners won't align; use `RECTANGLE`
8. **Negative shadow `offset`** corrupts files — use `angle: 270` with positive offset for upward shadows

---

## Design Principles

### Color Approach
- Pick a **bold, content-informed palette** — not generic blue
- One color dominates (60–70% visual weight) with 1–2 supporting tones and one sharp accent
- Dark backgrounds for title + conclusion slides, light for content ("sandwich"), or dark throughout

### Suggested Palettes

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| Midnight Executive | `1E2761` navy | `CADCFC` ice blue | `FFFFFF` |
| Teal Trust | `028090` teal | `00A896` seafoam | `02C39A` mint |
| Charcoal Minimal | `36454F` charcoal | `F2F2F2` off-white | `212121` black |
| Coral Energy | `F96167` coral | `F9E795` gold | `2F3C7E` navy |
| Ocean Gradient | `065A82` deep blue | `1C7293` teal | `21295C` midnight |

### Typography

| Element | Size |
|---------|------|
| Slide title | 36–44pt bold |
| Section header | 20–24pt bold |
| Body text | 14–16pt |
| Captions | 10–12pt muted |

Pair an interesting header font (Georgia, Trebuchet MS, Cambria) with a clean body font (Calibri).

### Per-Slide Layout
Every slide needs a **visual element** — image, chart, icon, or shape. Text-only slides are forgettable. Options:
- Two-column (text left, visual right)
- Icon + text rows (icon in colored circle, bold header, description)
- 2×2 or 2×3 grid
- Large stat callouts (60–72pt number, small label below)
- Timeline / process flow with numbered steps

### Avoid
- ❌ Repeating the same layout slide after slide
- ❌ Centering body text (left-align paragraphs; center only titles)
- ❌ Accent lines under titles (hallmark of AI-generated slides — use whitespace instead)
- ❌ Low-contrast elements (icons AND text need strong contrast)
- ❌ Text-only slides

---

## Visual QA (Required)

**Assume there are problems. Your first render is almost never correct.**

### Convert slides to images (Windows)

```powershell
# Requires LibreOffice and poppler (pdftoppm)
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
# Creates slide-01.jpg, slide-02.jpg, etc.
```

### What to check on every slide

- Overlapping elements (text through shapes, stacked elements)
- Text overflow or cut off at edges
- Decorative lines designed for single-line title but title wrapped to two lines
- Elements too close (< 0.3" gaps) or nearly touching
- Uneven gaps (large empty area vs cramped)
- Insufficient margin from slide edges (< 0.5")
- Low-contrast text or icons
- Leftover placeholder content

### Verification loop

1. Generate → convert to images → inspect
2. **List issues found** (if none, look harder)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass finds no new issues

### Content QA

```powershell
python -m markitdown output.pptx
# Check for leftover placeholder text
python -m markitdown output.pptx | Select-String -Pattern "xxxx|lorem|ipsum"
```

---

## Dependencies Summary

```powershell
pip install "markitdown[pptx]"    # text extraction
pip install Pillow                # thumbnail grids
npm install -g pptxgenjs          # create from scratch
npm install -g react-icons react react-dom sharp  # icons
# LibreOffice: https://www.libreoffice.org/download/
# Poppler (pdftoppm): https://github.com/oschwartz10612/poppler-windows/releases/
```
