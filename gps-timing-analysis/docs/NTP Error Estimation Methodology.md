# NTP Error Estimation Methodology

**Occultation Tools — NTP Timing Analysis**
*Reference document for `ntp_analysis_core.py`, `analyze_ntp_timing_accuracy.py`, and `gps_pps_comparison.py`*

---

## Overview

This document explains every calculation used in the NTP Timing Analysis tool to estimate how accurately a PC clock tracks UTC.  It is intended for both:

- **Occultation observers** who need to understand the timestamp correction applied to their recordings and the associated uncertainty, and
- **Technically-minded users** who want a formal account of the underlying mathematics.

Each method is explained at three levels: plain English, formal mathematics, and the Python code that implements it.  The document is structured from simple to complex.  **If you are an occultation observer looking for the bottom line, start with the Quick Reference below, then read Part 2 (the PIT estimator).**

---

## Quick Reference — Choosing the Right Method

| Your question | Method |  Where to read |
|---|---|---|
| **What correction do I apply to my observation timestamps?** | **PIT estimator** | **Part 2** |
| What was the maximum possible error at my recording time? | PIT $U_{\text{expanded}}$ + Meinberg delay check | Part 2, Part 3 |
| Is my timing setup good enough overall? | Interpretation C or D | Part 1 |
| What is the worst case over the whole day? | Variant G | Part 1 |
| Simplest audit-friendly single figure? | Variant F or B | Part 1 — reference only |
| Could a different server have done better? | PIT alternative estimate | Part 2, Step 3a |

**For occultation observers the PIT estimator is always the primary method.**  The whole-day methods (A–G) characterise your setup for records and reports; the PIT correction is what you actually apply to your timestamps.

---

## Background

This document is derived from the analysis in
`ntp_traceability.md` (located in the `occultation-ntp-installer` repository),
which examined Australia's National Measurement Institute (NMI) procedure
*"Making PC Time Traceable"*.  The NMI procedure described how to combine
loopstats and peerstats log data into a timing uncertainty estimate, but left
several important ambiguities about which statistical treatment was intended.

This toolset implements **eight distinct methods** — labelled A through G and
the dedicated **Point-in-Time (PIT)** estimator — covering the full range of
reasonable interpretations of the NMI procedure plus the occultation-specific
correction method.

---

## The Most Important Distinction: Two Different Questions

There are fundamentally **two different questions** this toolset can answer,
and they are answered by different methods.

---

### Question 1 — "How accurately does my PC clock track UTC over a whole day?"

**Shown in the analysis report: Interpretations C, D and Variants E, G.**  Interpretations A, B and Variant F are also computed and available in the JSON export; their detailed descriptions appear in the [Reference Only](#reference-only--not-shown-in-the-analysis-report) section of Part 1.

These methods analyse a full day's worth of NTP log data and produce an overall
characterisation of how well the PC clock performed.  They are useful for:

- Demonstrating that your timing setup meets a claimed accuracy standard
- Comparing performance across different configurations (local NTP pool,
  GPS-disciplined server, etc.)
- Generating the traceability record required for meteor timing or other
  observations where a formal accuracy claim must be lodged

**These methods do NOT tell you what the offset was at any specific moment.**
They give you a single number representing the "typical" accuracy over the
whole observation period.

---

### Question 2 — "What was the offset at the exact moment of my recording, and how do I correct my timestamps?"

**Answered by: the Point-in-Time (PIT) estimator**

For an occultation observation, you recorded video frames whose embedded
timestamps came from the PC clock.  You know NTP was running, so the clock
was being continuously steered toward UTC — but by exactly how much was it
off at 23:14:07.3 UTC when the occultation happened?

The PIT method answers this precisely.  It:

1. Looks up the NTP log records immediately surrounding the observation time
2. Interpolates between them to estimate the offset at that exact moment
3. Calculates uncertainty from drift, network lag, and measurement noise
4. Produces a **correction to apply to your timestamps** and a **±confidence interval**

**This is the most important method for occultation timing.**  The resulting
correction is what you actually subtract from (or add to) your PC timestamps
when submitting an observation report.

---

## NTP Log File Fields

Before explaining the methods, here is what each field in the log files means.

### loopstats fields

| Field | Symbol | Meaning |
|---|---|---|
| MJD | — | Modified Julian Day (integer date) |
| sec\_of\_day | $t$ | Seconds past midnight UTC |
| offset | $\delta$ | How far the PC clock was from the NTP server at correction time (seconds). Positive = PC is ahead. |
| freq | $f$ | The frequency correction NTP is injecting into the kernel clock (ppm). This is the correction *already applied*, not uncompensated drift. |
| jitter | $j$ | Short-term noise in offset measurements — the RMS scatter of recent offsets (seconds) |

**Important:** `offset` is the **remaining residual clock error** measured at each NTP poll — it shows how far the PC clock was from UTC when NTP took that measurement.  NTP uses this to continuously steer the clock toward zero, but some residual always remains between polls.  The `jitter` field captures how noisily those successive offset measurements vary.  Do not confuse `offset` with `freq`: the frequency field records the rate correction NTP is *already applying* to the kernel clock, not an uncompensated drift.

### peerstats fields

| Field | Symbol | Meaning |
|---|---|---|
| MJD | — | Date |
| sec\_of\_day | $t$ | Time of measurement |
| server\_address | — | IP address of the reference server |
| status | — | NTP select code (see below) |
| offset | $\delta_p$ | Server's measurement of clock offset (seconds) |
| delay | $d$ | Round-trip network delay to the server (seconds) |
| dispersion | $\sigma_p$ | NTP's internal estimate of accumulated uncertainty at this peer (seconds) |
| jitter | $j_p$ | Short-term scatter in this peer's offset measurements (seconds) |

### NTP select codes

NTP assigns each peer a numeric status code based on how it evaluates them.
Only peers that passed all sanity checks are used in analysis.

| Code | Name | Meaning |
|---|---|---|
| 0–3 | reject / falseticker / excess / outlier | Failed some NTP test; not used |
| 4 | candidate | Passed sanity checking; eligible as backup |
| 5 | backup | Used as backup source |
| **6** | **sys.peer** | **The primary server currently disciplining the clock** |
| **7** | **pps.peer** | **The primary server is a PPS-locked source (best quality)** |

The analysis uses only peers with select code ≥ 4 (candidate or better).
The sys.peer (code 6 or 7) is the one whose offset is currently being applied
to the PC clock.

---

## Part 1: Whole-Day Clock Accuracy Methods (A – G)

These methods all operate on the **full set of log records for a day**.
They produce a single characterisation summary — not a moment-by-moment estimate.

**Displayed in the analysis report:** Interpretations C and D; Variants E and G.
**Computed but not displayed** (available in the JSON export; see the [Reference Only](#reference-only--not-shown-in-the-analysis-report) section below): Interpretations A and B; Variant F.

---

### Methods Shown in the Analysis Report

---

### Interpretation C — Statistical (Most Rigorous for Clock Accuracy)

#### Plain English

Rather than treating the mean offset as a single number, this interpretation
separates the offset into two distinct parts:

1. The **systematic bias** — the average signed offset.  If NTP consistently
   shows your clock being 0.2 ms fast, that 0.2 ms is a systematic error that
   could in principle be corrected.

2. The **random wander** — how much the offset varies around that average.
   This is captured by the standard deviation.

The delay uncertainty is treated the same as in B, but the delay variation
(standard deviation of the delay) is also included as an additional component
to account for path instability.

This is the most statistically complete view of whole-day PC clock accuracy.

#### Formal Definition

$$c_{\text{bias}} = \frac{1}{n}\sum_{i=1}^{n}\delta_i$$

$$u_{\text{wander}} = \sigma(\{\delta_i\})$$

$$u_{\text{asymmetry}} = \frac{\bar{d}/2}{\sqrt{3}}$$

$$u_{\text{delay\_variation}} = \frac{\sigma(\{d_j\})}{2}$$

$$u_{\text{server}} = \frac{3\;\mu\text{s}}{\sqrt{3}}$$

$$u_{\text{combined}} = \sqrt{u_{\text{wander}}^2 + u_{\text{asymmetry}}^2 + u_{\text{delay\_variation}}^2 + u_{\text{server}}^2}$$

$$U_{\text{expanded}} = 2\,u_{\text{combined}}$$

The PC clock time at any point during the day can be written as:

$$t_{\text{UTC}} = t_{\text{PC}} - c_{\text{bias}} \pm U_{\text{expanded}}$$

where $c_{\text{bias}}$ is a **known systematic offset** that could be
subtracted, and $U_{\text{expanded}}$ is the remaining uncertainty after
that correction.

#### Python

```python
c_bias              = mean(offsets)            # systematic bias (sign-preserving)
c_u_wander          = stdev(offsets)
c_u_asymmetry       = (mean(delays) / 2.0) / SQRT3
c_u_delay_variation = stdev(delays) / 2.0
c_u_server          = 3e-6 / SQRT3
c_u_combined = math.sqrt(
    c_u_wander**2 + c_u_asymmetry**2
    + c_u_delay_variation**2 + c_u_server**2
)
c_u_expanded = 2.0 * c_u_combined
```

---

### Interpretation D — NTP Native Statistics

#### Plain English

NTP already calculates internal quality statistics and records them in the log
files.  Interpretation D trusts those numbers directly:

- **loopstats jitter** ($j$): NTP's own estimate of residual offset scatter
- **peerstats dispersion** ($\sigma_p$): NTP's accumulated uncertainty bound
  for the peer chain all the way back to the reference clock (Stratum 1, GPS etc.)

These two components, combined with the network asymmetry term and server
uncertainty, give a self-consistent picture that uses NTP's own model.

#### Formal Definition

$$u_{\text{jitter}} = \overline{j} = \frac{1}{n}\sum_{i=1}^{n} j_i$$

$$u_{\text{dispersion}} = \overline{\sigma_p}$$

$$u_{\text{asymmetry}} = \frac{\bar{d}/2}{\sqrt{3}}$$

$$u_{\text{server}} = \frac{3\;\mu\text{s}}{\sqrt{3}}$$

$$u_{\text{combined}} = \sqrt{u_{\text{jitter}}^2 + u_{\text{dispersion}}^2 + u_{\text{asymmetry}}^2 + u_{\text{server}}^2}$$

$$U_{\text{expanded}} = 2\,u_{\text{combined}}$$

#### Python

```python
d_u_jitter      = mean(loop_jitter)
d_u_dispersion  = mean(dispersions)
d_u_asymmetry   = (mean(delays) / 2.0) / SQRT3
d_u_server      = 3e-6 / SQRT3
d_u_combined = math.sqrt(
    d_u_jitter**2 + d_u_dispersion**2
    + d_u_asymmetry**2 + d_u_server**2
)
d_u_expanded = 2.0 * d_u_combined
```

---

### Variant E — Minimal (Network Asymmetry + Measurement Scatter)

#### Plain English

The two irreducible sources of uncertainty when NTP is running: the network
path itself (which could be asymmetric), and how consistently NTP measures
the offset.  No server chain uncertainty is included because it is negligible
(~3 µs) compared to typical network delays.

This variant asks: "Given that NTP *is* running and disciplining the clock,
what is the minimum uncertainty we cannot improve further without changing
the network?"

#### Formal Definition

$$u_{\text{asymmetry}} = \frac{\bar{d}/2}{\sqrt{3}} \qquad u_{\text{meas}} = \sigma(\{\delta_i\})$$

$$u_{\text{combined}} = \sqrt{u_{\text{asymmetry}}^2 + u_{\text{meas}}^2}$$

$$U_{\text{expanded}} = 2\,u_{\text{combined}}$$

#### Python

```python
e_u_asymmetry   = (mean(delays) / 2.0) / SQRT3
e_u_measurement = stdev(offsets)
e_u_combined    = math.sqrt(e_u_asymmetry**2 + e_u_measurement**2)
e_u_expanded    = 2.0 * e_u_combined
```

---

### Variant G — Conservative Worst-Case Delay

#### Plain English

Identical to Variant E, but uses the **maximum** delay observed during the
day instead of the mean.  This guards against transient congestion bursts that
the mean smooths over.  Use this when you need to state a worst-case bound
rather than a typical accuracy figure.

#### Formal Definition

$$u_{\text{asymmetry}} = \frac{d_{\max}/2}{\sqrt{3}} \qquad u_{\text{meas}} = \sigma(\{\delta_i\})$$

$$U_{\text{expanded}} = 2\sqrt{u_{\text{asymmetry}}^2 + u_{\text{meas}}^2}$$

#### Python

```python
max_delay       = max(delays) if delays else mean_delay
g_u_asymmetry   = (max_delay / 2.0) / SQRT3
g_u_measurement = stdev(offsets)
g_u_combined    = math.sqrt(g_u_asymmetry**2 + g_u_measurement**2)
g_u_expanded    = 2.0 * g_u_combined
```

---

### Comparison of Whole-Day Methods

| | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| **Shown in report** | No | No | ✅ Yes | ✅ Yes | ✅ Yes | No | ✅ Yes |
| **Offset treatment** | Signed mean | Abs mean / √3 | Bias + stdev | NTP jitter | stdev | — | stdev |
| **Delay treatment** | Full mean | Half mean / √3 | Half mean / √3 | Half mean / √3 | Half mean / √3 | — | Half max / √3 |
| **Server chain** | None | ±3 µs | ±3 µs / √3 | Dispersion | None | Dispersion | None |
| **Delay variation** | No | No | Yes | No | No | — | No |
| **Typical result** | Variable | Mid | Mid–High | Mid | Smallest | Largest | High |
| **Best use case** | Comparison to NMI literal | Metrological report | Statistical precision | Audit-friendly | Conservative lower bound | Quick worst-case | Regulatory bound |
| **Sign cancellation risk** | **Yes** | No | No | No | No | No | No |

**Recommended for general use:** Interpretation C (most rigorous) and
Interpretation D (most auditor-friendly).  Variants E and G bracket the
plausible range.

> **Note on server uncertainty treatment:**  The 3 µs figure represents the assumed intrinsic dispersion bound of a high-quality NTP reference server (Stratum 1) — the maximum amount by which the server's own time may differ from UTC.  Because this is a rectangular half-width, the correct standard uncertainty is $3\,\mu\text{s}/\sqrt{3} \approx 1.73\,\mu\text{s}$, which is what Methods C and D apply.  Method B does not divide by $\sqrt{3}$, consistent with the literal NMI text which quotes the figure as if it were already a standard uncertainty.  This makes Method B slightly conservative on this one component by ~1.3 µs — a difference that is entirely negligible against network delays of 5–100 ms but is noted here for completeness.

---

### Reference Only — Not Shown in the Analysis Report

These methods are computed internally and included in the JSON export but do not appear in the on-screen analysis report.  They are documented here as a **data dictionary for the JSON export** and for comparison with the NMI source procedure.

---

### Interpretation A — Literal Reading of the NMI Procedure

#### Plain English

The simplest possible reading of the NMI procedure: take the mean of the
loopstats offsets as a stand-in for "drift", take the mean of the peerstats
delays as a stand-in for "synchronisation accuracy", and combine them using
the quadrature rule (square-root of sum of squares).

This is included for completeness and for comparison with any figures quoted
directly from the NMI document.  It has documented flaws: signed offsets can
cancel out, the delay is not halved, and no statistical distribution
correction is applied.

#### Formal Definition

Let $\{\delta_i\}$ be the loopstats offsets and $\{d_j\}$ be the peerstats
delays for selected peers over the analysis period.

$$\bar{\delta} = \frac{1}{n}\sum_{i=1}^{n} \delta_i \qquad \bar{d} = \frac{1}{m}\sum_{j=1}^{m} d_j$$

$$U_A = \sqrt{\bar{\delta}^2 + \bar{d}^2}$$

#### Python

```python
mean_offset_signed = mean(offsets)          # signed — cancellation risk
mean_delay = mean(delays)
a_uncertainty = math.sqrt(mean_offset_signed**2 + mean_delay**2)
```

#### Limitations

- **Sign cancellation**: positive and negative offsets cancel, giving a misleadingly small mean
- **Delay not halved**: the full RTT is used, not the one-way asymmetry bound
- **No distribution factor**: a rectangular distribution should be divided by $\sqrt{3}$
- **No confidence level defined**

---

### Interpretation B — Metrologically Consistent (What the NMI Meant)

#### Plain English

The NMI document itself, in a worked example (Application 2), halves the delay
and applies the $1/\sqrt{3}$ factor for a rectangular distribution.
Interpretation B applies those same corrections to the whole-day summary,
consistent with the document's own methodology.

The absolute mean of the offsets is used instead of the signed mean, to avoid
the cancellation problem in Interpretation A.  The NMI document states that a
high-quality NTP reference server (Stratum 1) has a typical intrinsic dispersion
bound of ±3 µs.  Metrologically this is a half-width of a rectangular
distribution, so the standard uncertainty is $3\,\mu\text{s}/\sqrt{3}$.  However,
Method B is a literal transcription of the NMI procedure, which quotes the figure
as a direct standard uncertainty without the $\sqrt{3}$ step.  Method B
therefore uses the 3 µs value as-is; the result is slightly conservative on this
component only (the difference is ~1.7 µs, negligible against network delays).

#### Formal Definition

$$u_{\text{offset}} = \frac{\overline{|\delta|}}{\sqrt{3}} \qquad \overline{|\delta|} = \frac{1}{n}\sum_{i=1}^{n}|\delta_i|$$

$$u_{\text{delay}} = \frac{\bar{d}/2}{\sqrt{3}}$$

$$u_{\text{server}} = 3\;\mu\text{s} \quad \text{(literal NMI: bound used directly, without }\sqrt{3}\text{)}$$

$$u_{\text{combined}} = \sqrt{u_{\text{offset}}^2 + u_{\text{delay}}^2 + u_{\text{server}}^2}$$

$$U_{\text{expanded}} = 2\,u_{\text{combined}} \quad (k=2,\ \approx\!95\%\ \text{confidence})$$

#### Python

```python
mean_offset_abs = mean([abs(v) for v in offsets])
b_u_offset  = mean_offset_abs / SQRT3          # SQRT3 = math.sqrt(3)
b_u_delay   = (mean(delays) / 2.0) / SQRT3
b_u_server  = 3e-6                             # 3 µs
b_u_combined = math.sqrt(b_u_offset**2 + b_u_delay**2 + b_u_server**2)
b_u_expanded = 2.0 * b_u_combined
```

---

### Variant F — NTP Dispersion Directly

#### Plain English

Use NTP's own dispersion field as the uncertainty estimate.  Dispersion is
NTP's conservative internal bound on how uncertain it thinks the time is,
accumulated from the reference clock all the way down the server chain.

This is the easiest figure to justify to an auditor because it comes directly
from NTP itself.  However, it tends to be larger than necessary because NTP
is deliberately conservative, and it does not directly account for network
path asymmetry.

#### Formal Definition

$$U_{\text{expanded}} = 2\,\overline{\sigma_p}$$

#### Python

```python
f_u_offset   = mean(dispersions)
f_u_expanded = 2.0 * f_u_offset
```

---

## Part 2: Point-in-Time (PIT) Offset Correction

**This is the method that matters most for occultation observers.**

The whole-day methods above cannot tell you what correction to apply to a
specific timestamp from a specific recording.  The PIT estimator was designed
specifically for that problem.

---

### What It Does (Plain English)

You recorded an occultation at some time $T$.  NTP was running the whole time.
The PIT estimator:

1. Finds the NTP log records on either side of $T$ and interpolates to get the
   *best estimate* of the offset at exactly $T$.
2. Calculates the uncertainty from three independent sources: clock drift
   between log entries, network path asymmetry, and measurement noise.
3. Combines these into a single expanded uncertainty interval.

The output is:

$$t_{\text{UTC}} = t_{\text{PC}} - \hat{\delta}(T) \;\pm\; U_{\text{expanded}}$$

where $t_{\text{PC}}$ is the raw timestamp from your PC clock and
$\hat{\delta}(T)$ is the estimated NTP offset at time $T$.

---

### Step 1 — Best-Estimate Offset at $T$

#### Plain English

Look up the last loopstats entry before the observation time, and the first
entry after it.  If both exist, draw a straight line between the two offset
values and read off the value at $T$.  If only the "before" entry exists
(observation is at the very end of data), use the last known offset directly.

**Why not use the `freq` field to project forward?**

The `freq` field records the frequency correction NTP is *already injecting*
into the kernel clock.  It is not a raw uncompensated drift rate — NTP
is actively applying it to steer the clock.  Using it to project the offset
forward as if it were a free-running drift would double-count a correction
that is already reflected in the subsequent offset measurement.

#### Formal Definition

Find $t_{\text{before}} \leq T$ (last loopstats record at or before $T$) and
$t_{\text{after}} > T$ (first record after $T$, if any).

**Case 1 — Interpolation (both records available):**

$$\alpha = \frac{T - t_{\text{before}}}{t_{\text{after}} - t_{\text{before}}}$$

$$\hat{\delta}(T) = \delta_{\text{before}} + \alpha\,\bigl(\delta_{\text{after}} - \delta_{\text{before}}\bigr)$$

**Case 2 — Extrapolation (only a record before $T$):**

$$\hat{\delta}(T) = \delta_{\text{before}}$$

#### Python

```python
# Interpolation (after record exists)
total_gap = gap_before_s + gap_after_s
fraction  = gap_before_s / total_gap if total_gap > 0 else 0.0
best_offset = before.offset + fraction * (after.offset - before.offset)

# Extrapolation (no after record)
best_offset = before.offset
```

---

### Step 2 — Drift Uncertainty $u_{\text{drift}}$

#### Plain English

Even with the best interpolation between two log entries, there is some
residual uncertainty because NTP does not correct the clock instantaneously
between entries.  The loopstats `jitter` field measures this residual noise.

When only the "before" record is available (extrapolating forward), the
uncertainty grows with time.  The `freq` field tells us how fast NTP has
been steering the clock, giving a bound on how far it could drift in the gap.

#### Formal Definition

**Case 1 — Interpolating:**

$$u_{\text{drift}} = \max\!\bigl(j_{\text{before}},\; j_{\text{after}}\bigr)$$

where $j$ is the loopstats jitter value.

**Case 2 — Extrapolating:**

$$u_{\text{drift}} = \max\!\left(\frac{|f \times 10^{-6} \times \Delta t|}{\sqrt{3}},\; j_{\text{before}}\right)$$

where $f$ is the frequency correction in ppm and $\Delta t = T - t_{\text{before}}$.

The $\sqrt{3}$ factor treats the residual drift as uniformly distributed over
$[0, f \cdot \Delta t]$ (rectangular distribution).  The `jitter` is used as
a floor because that is the irreducible measurement noise even when NTP is
perfectly synchronised.

#### Python

```python
# Case 1 (interpolating)
u_drift = max(before.jitter, after.jitter)

# Case 2 (extrapolating)
freq_drift_bound = abs(freq_ppm * 1e-6 * gap_before_s)
u_drift = max(freq_drift_bound / SQRT3, before.jitter)
```

---

### Step 3 — Network Path Asymmetry Uncertainty $u_{\text{asymmetry}}$

#### Plain English

When a time packet travels from an NTP server to your PC and back,
NTP measures the total round-trip time (the "delay" or RTT).  It assumes
the trip takes equal time in each direction and sets the clock accordingly.

But the network is rarely perfectly symmetric — the outbound and inbound
paths may have different speeds, congestion levels, or routing.  The worst
case is that *all* of the round-trip time was in one direction.  This means
the actual offset could be anywhere in the range $[-d/2,\, +d/2]$.

Assuming this error is uniformly distributed gives a standard uncertainty of:

$$u_{\text{asymmetry}} = \frac{d/2}{\sqrt{3}}$$

The tool collects the RTT values from the records of the **active selected
server** (the sys.peer) in the ±1 hour window around the observation time and
uses their mean.

**Geographic tightening (when server location is known):**
If the tool can determine the geographic location of the NTP server and the
observer, it computes the minimum one-way propagation delay from the
geographic distance at the speed of light through fibre
($v \approx 204{,}354$ km/s).  This portion of the delay is symmetric by
physics — light travel time is the same in both directions — so it can be
subtracted from the asymmetry bound:

$$b_{\text{asym}} = \max\!\left(\frac{\bar{d}}{2} - d_{\min},\; 0\right)$$

#### Formal Definition

Collect peerstats records from the active selected server within $[T - W, T + W]$
(default $W = 3600$ s).  Let $\bar{d}$ be the mean of their delay values.

$$b_{\text{asym}} = \frac{\bar{d}}{2} \qquad u_{\text{asymmetry}} = \frac{b_{\text{asym}}}{\sqrt{3}}$$

With geographic tightening (geographic distance $D$ km, fibre speed $v$ km/s):

$$d_{\min} = \frac{D}{v} \qquad b_{\text{asym}} = \max\!\left(\frac{\bar{d}}{2} - d_{\min},\; 0\right)$$

#### Python

```python
delays_near = [row.delay for row in network_peers]
mean_delay_near = mean(delays_near)
b_asym_raw = mean_delay_near / 2.0

# Geographic tightening (if server location resolved)
d_min_s = server_loc["d_min_s"]            # None if location unknown
if d_min_s is not None:
    b_asym = max(b_asym_raw - d_min_s, 0.0)
else:
    b_asym = b_asym_raw

u_asymmetry = b_asym / SQRT3
```

---

### Step 3a — Alternative Estimate from Candidate Peers

#### Plain English

NTP may be polling several servers simultaneously.  Only the best one at any
moment (the sys.peer, code 6 or 7) disciplines the clock.  But the other
servers that have passed NTP's quality tests (candidate or backup, codes 4–5)
also record their own independent offset measurements in peerstats.

Sometimes one of these other servers happens to have a much shorter round-trip
time (perhaps a closer server or a less congested path), which means its
asymmetry uncertainty is smaller.  The PIT estimator checks all candidate
peers near the observation time and reports the one with the lowest combined
uncertainty as an **alternative estimate**.

This can produce a better accuracy claim than the sys.peer estimate — but only
if the alternative peer's own delay and jitter genuinely produce a tighter
interval.

**Important constraint:** The alternative peer's offset and delay are always
used together.  You may not mix a candidate peer's smaller RTT into the
sys.peer's loopstats-derived offset.  Doing so would be metrologically invalid
because each server's offset measurement already incorporates assumptions about
its own path symmetry.

#### Formal Definition

For each non-sys.peer candidate server $k$ near $T$, compute:

$$b_k = \frac{d_k}{2} \qquad u_k^{\text{asym}} = \frac{b_k}{\sqrt{3}} \qquad u_k^{\text{scatter}} = j_k$$

$$u_k^{\text{combined}} = \sqrt{\left(u_k^{\text{asym}}\right)^2 + \left(u_k^{\text{scatter}}\right)^2}$$

$$U_k^{\text{expanded}} = \sqrt{(0.95\,b_k)^2 + (2\,u_k^{\text{scatter}})^2}$$

Select the peer $k^*$ minimising $u_k^{\text{combined}}$.  If
$U_{k^*}^{\text{expanded}} < U_{\text{expanded}}$ (the sys.peer result), report
$k^*$ as an improved alternative estimate.

#### Python

```python
for addr, (gap, row) in by_server.items():
    b_a   = row.delay / 2.0
    u_a   = b_a / SQRT3
    u_s   = row.jitter
    score = math.sqrt(u_a**2 + u_s**2)
    if best_score is None or score < best_score:
        best_score      = score
        alt_best_offset = row.offset
        alt_u_asymmetry = u_a
        alt_u_scatter   = u_s
        alt_u_combined  = score
        alt_u_expanded  = math.sqrt((0.95 * b_a)**2 + (2.0 * u_s)**2)
```

---

### Step 4 — Measurement Scatter $u_{\text{scatter}}$

#### Plain English

Within the ±1 hour window around the observation, the loopstats file shows
many offset readings.  The spread (standard deviation) of those readings
captures everything that causes the offset to vary in real time: real network
path changes, local clock noise, NTP's own polling jitter, and any slow drift
not modelled by the frequency field.

#### Formal Definition

Collect loopstats records within $[T - W, T + W]$:

$$u_{\text{scatter}} = \sigma\!\left(\{\delta_i : |t_i - T| \leq W\}\right)$$

If fewer than two records are available in the window, $u_{\text{scatter}} = 0$.

#### Python

```python
near_loop    = [row for row in sorted_loop if abs(loop_abs_sec(row) - query_abs) <= window_seconds]
near_offsets = [row.offset for row in near_loop] if near_loop else [before.offset]
u_scatter    = stdev(near_offsets) if len(near_offsets) >= 2 else 0.0
```

---

### Step 5 — Combined and Expanded Uncertainty

#### Plain English

The three components — drift, asymmetry, and scatter — are combined in
quadrature (the standard technique when uncertainties are independent).  This
gives $u_{\text{combined}}$ at approximately the 68% confidence level (k=1).

For the expanded uncertainty at ~95% confidence (k=2), the treatment must
account for the fact that the asymmetry component follows a **rectangular
distribution** while drift and scatter are approximately Gaussian.  Applying
$k=2$ uniformly would overstate the expanded interval for the rectangular
term (a uniform distribution's "95%" coverage is at 0.95×bound, not 2×stdev).

The correct expansion combines the two distribution types in quadrature:

$$U_{\text{expanded}} = \sqrt{(0.95\,b_{\text{asym}})^2 + (2\,u_{\text{stat}})^2}$$

This guarantees that $U_{\text{expanded}} \leq b_{\text{asym}} = \bar{d}/2$:
the reported interval never claims to be tighter than the hard physical
ceiling set by the RTT.

#### Formal Definition

$$u_{\text{combined}} = \sqrt{u_{\text{drift}}^2 + u_{\text{asymmetry}}^2 + u_{\text{scatter}}^2}$$

$$u_{\text{stat}} = \sqrt{u_{\text{drift}}^2 + u_{\text{scatter}}^2}$$

$$U_{\text{expanded}} = \sqrt{(0.95\,b_{\text{asym}})^2 + (2\,u_{\text{stat}})^2} \quad (\approx\!95\%\ \text{confidence})$$

#### Python

```python
u_combined = math.sqrt(u_drift**2 + u_asymmetry**2 + u_scatter**2)

u_stat     = math.sqrt(u_drift**2 + u_scatter**2)
u_expanded = math.sqrt((0.95 * b_asym)**2 + (2.0 * u_stat)**2)
```

---

### Step 6 — Applying the Correction

#### Plain English

The NTP offset tells you how far your PC clock was from UTC. To get the true
UTC time of your observation, subtract the estimated offset from the recorded
PC timestamp:

$$t_{\text{UTC}} = t_{\text{PC}} - \hat{\delta}(T) \;\pm\; U_{\text{expanded}}$$

A positive offset means the PC clock was fast (ahead of UTC), so subtracting
it shifts the timestamp earlier.  A negative offset means the clock was slow;
subtracting it shifts the timestamp later.

---

### PIT Uncertainty Budget — Typical Examples

**Internet NTP server, RTT ≈ 50 ms, interpolating between records 64 s apart:**

| Component | Typical value |
|---|---|
| $u_{\text{drift}}$ (max jitter at surrounding records) | ±0.1 – 0.5 ms |
| $u_{\text{asymmetry}}$ (RTT = 50 ms) | ±14.4 ms |
| $u_{\text{scatter}}$ (stable NTP) | ±0.1 – 1 ms |
| **$U_{\text{expanded}}$ (~95%)** | **≈ ±24 ms** |

**Local GPS-disciplined stratum-1 server, RTT ≈ 1 ms:**

| Component | Typical value |
|---|---|
| $u_{\text{drift}}$ | ±5 – 50 µs |
| $u_{\text{asymmetry}}$ (RTT = 1 ms) | ±0.3 ms |
| $u_{\text{scatter}}$ | ±0.05 – 0.2 ms |
| **$U_{\text{expanded}}$ (~95%)** | **≈ ±0.5 ms** |

The network asymmetry term ($\bar{d}/2/\sqrt{3}$) dominates in virtually all
internet cases.  The single most effective way to improve accuracy is to
reduce the RTT — by using a closer server or a local GPS source.

---

### PIT Limitations

| Limitation | Impact |
|---|---|
| Linear interpolation | Assumes offset changes linearly between log entries. Non-linear jumps (NTP step corrections) are partially accounted for by the `jitter` floor. |
| Extrapolation at end of data | When the recording extends past the last loopstats entry, uncertainty grows via the `freq` drift term. |
| Rectangular asymmetry model | Assumes the one-way path split is uniformly distributed between 0 and $d$. For known-symmetric paths (local LAN), $b_{\text{asym}}$ could be reduced. |
| Long NTP poll intervals | At poll interval 1024 s, the gap between log entries is ~17 min. Interpolation is less precise; watch `gap_before_s` in the report. |
| Server chain uncertainty | The uncertainty of the reference server itself (~±3 µs for a tier-1 Stratum 1) is not included. It is negligible against network uncertainty for all internet usage. |
| Candidate-peer staleness | The alternative estimate uses the peerstats record nearest in time to T. The time gap is reported as `alt_gap_s`. |

---

## Part 3: Reading the Meinberg Time Server Monitor — Maximum Error Estimation

The Meinberg NTP Time Server Monitor (and the `ntpq -p` command it is based on)
shows a live status panel for each NTP peer.  This section explains what each
displayed value means for estimating the maximum possible timing error **at
the time of observation**, without needing to run log file analysis.

This is intended as a quick sanity check at the telescope, not a substitute
for full log-based analysis.

### Meinberg Status Panel Fields

The three fields shown in the Meinberg NTP Status panel:

| Field | What It Means |
|---|---|
| **Offset** | NTP's current estimate of how far the PC clock is from UTC (milliseconds). Positive = PC is fast. This is *not* the residual error — it is the correction being applied right now. After NTP applies this correction, the remaining error is captured in Jitter. |
| **Delay** | Current round-trip time (RTT) to the server in milliseconds. This is the single most important number for maximum-error estimation. |
| **Jitter** | Short-term variation in offset measurements (milliseconds, RMS). Represents how consistently NTP can measure the offset — i.e., residual noise after correction. |

**NTP Dispersion** — the accumulated uncertainty bound propagated from the reference clock down through the stratum chain — is **not shown** in the Meinberg panel.  It appears in the peerstats log files and in the full analysis report (Interpretation D).

Dispersion cannot be read directly from the three panel fields, but for practical purposes:
- NTP guarantees **Dispersion ≥ Jitter** — Jitter is always a lower bound
- Dispersion grows between polls at ~15 µs per second and resets at each poll.  After a 64 s poll interval this adds ~1 ms; after 1024 s it adds ~15 ms.  The Jitter value you see captures the same measurement noise and is typically within a factor of 2 of the dispersion for a healthy connection.
- The variation you observe in the Offset field from one panel refresh to the next is essentially Jitter — not Dispersion, but a close proxy for it.
- For any internet server, the Delay/2 asymmetry term is 5–50× larger than dispersion, so dispersion adds negligibly in quadrature.  The quick formula below therefore omits it.

### Quick Maximum-Error Guide

**Hard physical maximum error:**

At any instant, the worst-case error from network path asymmetry alone is:

$$E_{\max} = \frac{\text{Delay}}{2}$$

*No NTP analysis can produce a guaranteed error smaller than $\text{Delay}/2$.*
If the Meinberg panel shows Delay = 60 ms, the maximum possible error from
asymmetry alone is ±30 ms, regardless of what the Offset field shows.

**Practical estimate from what you can read on screen:**

A useful rule-of-thumb for the approximate expanded uncertainty at the time of
observation, using only the two uncertainty-relevant displayed values:

$$U_{\text{approx}} \approx \sqrt{\left(\frac{\text{Delay}/2}{\sqrt{3}}\right)^2 + \text{Jitter}^2}$$

Dispersion is omitted here because it is not shown in the panel and, for any internet
server, is much smaller than the Delay/2 asymmetry term (see the note on Dispersion above).
If you have run the full log analysis and see a large Dispersion value in the report
(> 10 ms), add it in quadrature: $U \approx \sqrt{(\text{Delay}/2/\sqrt{3})^2 + \text{Jitter}^2 + \text{Dispersion}^2}$.

Typical quick interpretation:

| What you see | Likely maximum error |
|---|---|
| Delay < 5 ms, Jitter < 0.3 ms | ±2 ms (local server) |
| Delay 10–30 ms, Jitter < 1 ms | ±10 – 18 ms (regional server) |
| Delay 50–100 ms, Jitter < 2 ms | ±30 – 60 ms (international server) |
| Delay > 100 ms or Jitter > 5 ms | > ±60 ms — likely unsuitable for precision timing |

**What the Offset field tells you:**

The Offset value on screen is NTP's *current estimate* of how far the clock is
from UTC — it does not tell you what the offset *was* at an earlier observation
time.  For logging and correction purposes, the Offset field is only useful at
the exact moment you look at it.  For retrospective analysis of recorded data,
you must use the log file methods above.

**What to look for during an occultation:**

At the time of your recording, a healthy NTP configuration should show:

- **Delay:** stable, not fluctuating wildly between readings
- **Jitter:** small and stable (< 2 ms for internet NTP, < 0.1 ms for GPS)
- **Offset:** small (< 10 ms for internet NTP, < 0.5 ms for GPS).  If the
  Offset is stepping suddenly or exceeding 100 ms, NTP may be adjusting after
  a disruption and timing accuracy is degraded until it stabilises.

If the Delay is large (> 50 ms), the uncertainty budget is dominated by
asymmetry and the Jitter value matters relatively little.  The only path to
better accuracy in that case is to use a closer or GPS-disciplined server.

---

## Summary

There are two fundamentally different things this tool can tell you:

1. **Whole-day accuracy (Methods A–G):** How well did the PC clock track UTC over a full observation day?  Use the Interpretation C or D figures for reports and records.

2. **Point-in-time correction (PIT):**  What was the actual offset at the exact moment of your recording, and what uncertainty should you quote?  This is the number you subtract from your recorded PC timestamps to get UTC.

The network round-trip delay (RTT) is the single most important factor in both cases.  The hard physical maximum error from path asymmetry is always $\bar{d}/2$ — no analysis can improve on that.  The fastest route to better timing accuracy is to reduce RTT by using a closer or GPS-disciplined server.

If in doubt, report both the PIT correction and the whole-day summary side by side, noting which server was active at the time of the event.
