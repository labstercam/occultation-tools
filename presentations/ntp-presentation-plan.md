# NTP Timing for Occultations — Presentation Plan
**Format:** 30-minute Zoom | **Goal:** Change community attitudes; establish NTP as the standard first choice for new observers

> **Audience note:** This is a complex mixed room. Read the Audience Strategy section before planning language or emphasis.

---

## The Core Communication Challenge

The audience holds a belief: *"NTP is not accurate enough for occultations."* This is a **belief change** problem, not an information delivery problem. Every decision about structure, visuals and language must serve that goal.

The trap to avoid: a bullet-heavy overview talk that informs but doesn't persuade. The current draft reads as a feature list. It needs a **narrative with tension and resolution**.

Additional complexity: this room contains both your most powerful ally (Dave Herald, who has already said ~5ms is good enough) and potential sceptics (hardware developers who have invested years in GPS camera products). These audiences pull in different emotional directions but must receive the same talk. The solution: position NTP and GPS hardware as serving different access tiers — never as competing solutions.

---

## Audience Strategy

Understanding each segment before writing a slide is essential.

### TTOA committee members — key policy target
- Hold formal listing decisions
- Respond to data and verifiability, not enthusiasm
- Primary message: *"The evidence is here, the tools are free, the accuracy is documented — listing NTP increases chord coverage per campaign at zero cost to organisers."*
- The GPS PPS comparison result (internet NTP measured against GPS ground truth) is their key piece of evidence

### Dave Herald — IOTA worldwide coordinator (will be in the room)
- Already on your side. Personal communication: ~5ms is good enough; traceability and reliability matter more than raw accuracy
- He is not a target to convince — he is an ally to activate
- Quote him early and honestly. When the audience hears his name and he is in the room, it shifts the dynamic from "presenter making a claim" to "presenter reporting expert consensus"
- Do not put him on the spot mid-talk; let him respond in Q&A naturally if he chooses to

### Hardware developers — IOTA-VTI, Astrid (potentially defensive)
- Have invested years in GPS camera products. Any "NTP is good enough" talk can read as "your hardware isn't needed"
- Critical framing: NTP is the entry tier that grows the observer community — the pool from which hardware customers come
- The upgrade path (NTP → GPS PPS → GPS flasher → dedicated camera) makes hardware products the *destination*, not the competition
- Emphasise: GPS cameras remain best for high-value events, close calls, and events needing sub-1ms accuracy; NTP covers the majority of events where 3–5ms is sufficient
- A growing NTP observer base means more people who understand what the hardware does — and more buyers

### Analog VTI-only users
- Many will not know CMOS camera workflow, SharpCap, ROI, frame rates, or "occultation software" at all
- Do not assume familiarity with USB cameras or the CMOS pipeline
- Frame NTP as: *"the modern equivalent of what VTI users already do — your VTI stamps each frame with GPS; NTP gives a CMOS computer camera an equivalent discipline"*
- Acknowledge VTI works well. Do not position NTP as better — position it as a parallel valid path for a different setup

### Beginners and general astronomers
- Need more context before evaluating precision claims
- Key message: "You need less hardware than you think, and you can verify your accuracy"
- The upgrade path slide is their roadmap

### The unifying message (works for every segment)
> *"More observers, better data, lower barrier — without compromising on accuracy verification or traceability."*

- Beginners hear: *I can participate*
- TTOA committee hears: *better campaign coverage*
- Hardware developers hear: *bigger community, more customers*
- VTI users hear: *my workflow is validated; this is a parallel path*
- Dave Herald hears: *this formalises what I've known to be true*

---

## Proposed Narrative Arc

**Working title: "You Already Have Everything You Need"**

The story beats:

| Beat | What happens | Time |
|------|-------------|------|
| **Hook** | Open with the real cost of the status quo — not hardware cost, but *lost observations*. How many events go unrecorded because people assume they can't do it? | 2 min |
| **Establish the belief** | Name the assumption out loud: "NTP can't be accurate enough." This respects the audience and sets up the demolition. | 1 min |
| **Demolish with data** | Show real loopstats/NTP monitor data. Concrete numbers. This is the pivot of the whole talk. | 6 min |
| **The math they never hear** | Walk through the uncertainty budget for a real occultation. Show where 5ms fits. | 4 min |
| **The traceability argument** | NTP is *verifiable*. Show the GPS vs NTP Testing tool. This is the professional credibility argument. | 4 min |
| **The workflow** | 10-minute install. Free. Camera delays estimated without a flasher. | 5 min |
| **The upgrade path** | NTP → GPS PPS → GPS flasher. Nobody is locked in. Each step is optional. | 3 min |
| **Call to action** | Specific ask: for beginners, for TTOA, for campaign coordinators. | 3 min |
| **Q&A** | Buffer time built in. | 2 min |

---

## Slide-by-Slide Content Plan

### Slide 1 — HOOK (not a title slide)
**Don't open with the agenda.** Open with the problem they recognise.

**Option A (emotional):** A map of a predicted occultation path with coverage gaps over populated areas.
Caption: *"These cities had no observer. Not because no one had a camera. Because no one thought they could time it."*

**Option B (challenge):** A single question, large on screen:
*"How accurate is your PC clock right now?"*
(Then reveal: on a good NTP setup, you probably know to within 2–5 ms.)

**Hook: Option A — confirmed.**

**[ASSET AVAILABLE: `gps-timing-analysis/docs/occultation-map.png`]** — Occultation path map showing the shadow track crossing Queensland, Brisbane, and the lower South Island of New Zealand. Use full-slide or near-full-slide. No title slide preceding it — open cold on the map.

**Hook line (exact):**
> *"No observations. Not because no one had a camera. Because no one thought they could time it."*

Delivery note: let the map sit for 2–3 seconds in silence before the line. The populated coastline running through the empty path does the work — the words confirm what the audience already feels looking at it. After the line, pause again before moving on.

**Dave Herald opener (alternative — retain as backup):** Opening directly with his quote works if the map slide is not available or doesn't render cleanly on Zoom. *"I want to start with something Dave Herald told me. He's coordinated more occultation campaigns than anyone alive, and he said: 'About 5ms is accurate enough. What matters most is traceability — knowing that it worked, and knowing if it failed.' Tonight I want to show you we can achieve exactly that."*

---

### Slide 2 — The barrier is wrong
Frame the problem differently than cost alone.

Current text says: "High up-front cost." That's true but incomplete. The deeper barrier is:
- People assume NTP isn't good enough, so they never investigate
- The complexity narrative puts them off before they start
- The "right" answer (GPS camera, Astrid) is presented as the only answer

**Visual needed:** A side-by-side ladder:
```
Wants to try occultations
         ↓
Searches for "how to time occultations"
         ↓
Finds: "you need GPS timing / VTI / dedicated camera"
         ↓
Sees cost: $500–$1,200+
         ↓
Closes the tab.
```
**The talk reframes** this: there's a step 0 they weren't told about.

**Anchor sentence for VTI-only users (deliver verbally while the ladder is on screen, before moving to Slide 3):**
> *"A CMOS camera records video with timestamps from the PC clock. So the PC clock accuracy is the timing accuracy. NTP is the software that disciplines that clock."*

This one sentence is sufficient. It ensures VTI-only observers understand why the PC clock matters at all, without slowing down anyone who already knows. Do not put it on a slide — say it as a spoken transition between slides 2 and 3.

---

### Slide 3 — What NTP actually achieves ⭐ (MOST IMPORTANT SLIDE)
This is the pivot of the talk. It needs real data, not claims.

**Content required:**
- A screenshot of NTP Server Monitor showing a real session: delay 3–8ms, jitter 1–2ms, offset ±1–3ms
- The simple rule: *time error ≤ half the delay* (the bounding argument, not an average)
- The typical achievable result: **sub-1ms to low-ms** on domestic fibre with GPS-referenced Stratum 1 servers — far better than the "±100ms" assumption
- Comparison to what people fear: "±100ms" is dial-up, default Windows time service, or pool servers without optimisation

**Key line to land:** *"The NTP you set up for your PC by default is not the NTP we're talking about."*

**[ASSET AVAILABLE: `gps-timing-analysis/docs/ntp-server-monitor-status.png`]** — Meinberg NTP Time Server Monitor 1.04, live status from the home observatory PC on fibre. Key numbers to call out on the slide:
- **Current local NTP Status: Sync to: 103.70.25.21 Offset: -0.035ms Stratum: 2** — that headline is 35 *micro*seconds, not milliseconds
- Selected server (\*): refid GPS, Stratum 1, Offset -0.035ms, Jitter 0.338ms, Reach 377 (perfect 8/8 polling history)
- Other active GPS-referenced servers: offsets of 0.290ms, -0.361ms — all well under 1ms
- Reach code 377 (octal) = binary 11111111 = every poll for the last 8 intervals responded — demonstrates reliability, not just accuracy
- The red rows (hyphen flag) are servers NTP has evaluated and set aside — show the algorithm is actively choosing the best source

**Presentation note:** The -0.035ms headline is unexpectedly strong — better than most audiences will predict. Lead with it ('thirty-five *micro*seconds'), then let the table show the full picture. The Reach 377 column quietly answers the reliability objection without needing a separate slide.

---

### Slide 4 — "But is 5 ms good enough?" — The uncertainty budget
The audience needs to see NTP's contribution placed *in context* of total observation uncertainty.

For a typical main-belt asteroid occultation the exposure would typically be ~100 ms for a brightish mag 12-13 star. Uncertainty in D/R will be roughly half the exposure so ~50 ms.

The measurement undertainty of the D/R from light curve is usually much greater than the timing uncertainty. Uncertainties of 5-10 ms in the PC clock or timing will have negligible affect on the D/R Uncertaintain

**Suggested visual:** An uncertainty stack bar for a typical event:
```
Source                         Uncertainty
──────────────────────────────────────────
NTP clock (from NTP Clock Accuracy tool)  ±5 ms (PIT estimate from logs)
Camera line delay (measured)   ~1 ms  
Camera frame delay (estimated) ±2 ms
──────────────────────────────────────────
Total (RSS)                    ±5-6 ms
```

The **NTP Clock Accuracy** tool in Occultation Manager produces the PIT estimate that fills the first row — it is not a generic assumption, it is a calculated value from the actual NTP log for that session.

Compare this to: A 5ms timing uncertainty is **not the limiting factor for most events.**

**Key authority — ANSWERED:** Dave Herald, IOTA worldwide coordinator and the analyst of more occultation results globally than anyone else, has stated in personal communication:

> Paraphrased *"About 5ms is accurate enough for most observing situations. Reliability and traceability are more important than the raw accuracy number — knowing when your timing has failed matters more than achieving the absolute lowest number."*

This is more powerful than any published standard because it comes from the person who receives and analyses global results — and he will be in the room. Name him, quote him, let it land. Then show the tools that achieve and verify that standard.

---

### Slide 5 — "How do I know MY setup is accurate?" — Traceability
This is the professional credibility argument. NTP is verifiable. GPS cameras are assumed correct but rarely verified.

**The key tool for this slide: NTP Clock Accuracy (in Occultation Manager)**
This tool analyses the NTP log files and computes an estimated offset and timing error at a **specific Point In Time** — intended to be the exact moment of the event D/R. This transforms "my NTP setup was generally good that night" into a documented, reportable claim: *"At 14:23:07.4 UTC, my estimated clock offset was −0.04 ms ± 0.3 ms."* That number can go into the observation report. It is the traceability chain made concrete.

This is something most GPS-camera users do *not* do. The NTP workflow with this tool produces *better documented* uncertainty than an assumed-correct GPS camera with no post-hoc verification.

**Content:**
- Show the NTP Clock Accuracy tool output: offset estimate and error bounds at the D/R Point In Time
- Show the GPS vs NTP Testing tool: internet NTP servers measured against GPS PPS ground truth — validates the NTP offset chain back to UTC
- Key message: *"You have a calibration chain. You can show your work — down to the exact second of the event."*

**[ASSET AVAILABLE: `gps-timing-analysis\docs\ntp-accuracy-example1.png` Screenshot from NTP Clock Accuracy tool showing a PIT analysis for an event. Figure in green at the bottom are the PIT offset and estimated  accuracy. `gps-timing-analysis\docs\ntp-accuracy-example2.png` is the detailed analysis of all the server stats for this event]**


**[ASSETS AVAILABLE: `gps-timing-analysis/docs/gps-camera-calibration.png` and `gps-stability-test.png`]** — Can supplement to show the complete calibration chain: NTP accuracy verified against GPS → camera delay measured and stable over 9 hours.

---

### Slide 6 — NTP-Installer A 10-minute install
Show screenshot of ntp installer. Asset `gps-timing-analysis\docs\NTP-Installer.png`

**Content:**
- Double-click `.cmd`, accept UAC
- Automatic mode: Meinberg NTP + Server Monitor installed
- Country-specific national standard servers configured
- NTP working within seconds, stable within 15–30 minutes
- Optional GPS PPS setup — same installer, one more step

**Installer highlights worth calling out:**
- 35 countries covered with national standard servers for TRACEABILITY to UTC
- QoS priority (DSCP 46) for NTP traffic — reduces timestamp jitter on Windows
- Standard-user layout so you don't need admin rights after install
- Desktop "Restart NTP" shortcut included

**Key message:** *"You can set this up in the time it takes to make a toasted cheese sandwich."*

Insert live  link to https://github.com/labstercam/occultation-ntp-installer
---

### Slide 7 — Camera delays without a flasher
Reframe: this is not a limitation, it's a solvable problem.

**Content:**
- The max-FPS method: measure the line delay from maximum frame rate at your recording settings
- Formula: `per_line_delay = (1/fps) / ROI_height × 1000 ms`
- Frame delay estimate: ~2 ms for small sensors, small ROI (USB3 connected)
- The Camera Timing Setup "Approximate Delays" tool in Occultation Manager does this automatically
- Where to get measured values for your camera: community shared calibrations, other observers with a flasher
- Cameras to avoid: USB 2.0, large sensor cameras (4/3+ or larger) with large ROI

**[ASSET AVAILABLE: `gps-timing-analysis\docs\camera-coefs.png`]** Shows the measured coefficients using max-FPS method


### Slide 7B — Camera delays with a flasher
Can be done with a $10 GPS USB receiever, HiLetGo VK172 or similar.

**[ASSET AVAILABLE: `gps-timing-analysis/docs/gps-camera-calibration.png`]** — Camera Timing Setup, Line Delay Calibration tab. Actual result: *"Line delay of 12.8 - 0.028 × Y ms, R² = 0.990 — Excellent."* Clean linear fit through GPS flash measurements across the sensor height. Use this to show the flasher calibration method working with high precision. R²=0.990 is a strong, easy-to-read number even for non-technical audience members.

### Slide 7C — Stability of NTP compared to GPS flasher
Test of NTP offset against GPS flasher showing excellent stability.

**[ASSET AVAILABLE: `gps-timing-analysis/docs/gps-stability-test.png`]** — Camera Timing Setup, Long Term Timing Stability tab. **27,042 GPS flashes recorded over 9 hours. Mean: 7.377ms (95% CI: ±0.006ms), Median: 7.381ms, Std Dev: 0.465ms, Range: 6.232–8.491ms.** Upper chart shows delay stable over time; lower chart shows a tight histogram centred at 7.38ms. This is the definitive answer to *"how do you know the camera delay is stable?"* — 9 hours and 27,000 direct GPS-flash measurements, with sub-millisecond precision on the mean. The ±0.006ms 95% confidence interval is a number that lands hard even in a sceptical room.

---

### Slide 8 — The complete beginner stack
One slide, everything they need, total cost.

| Component | What | Cost |
|-----------|------|------|
| PC | Windows laptop or desktop | Already own |
| Camera | Any USB3 planetary camera | Already own or ~$US179 for ToupTek G3M662M|
| SharpCap | Capture software | Free to get started, but need Pro |
| SharpCap | Capture software | Pro licence ~$20 |
| Meinberg NTP | Clock discipline | Free |
| NTP Installer | All-in-one setup | Free |
| Occultation Manager | Events, sequences, reports | Free |
| **Total** | | **$20 new cost** |

**Then the upgrade row:**
| GPS NMEA receiver | Generic purchase | ~$20–50 AUD | PPS is better|
| GPS PPS receiver | DIY build | ~$50–80 AUD | Excellent timing |
| Basic GPS flasher | HiLetgo VK172 | ~$10 AUD | Works but dedicated flasher is better |
| Simple GPS flasher | DIY build | ~$20–50 AUD | Works fine |
| Dedicated GPS flash timer | DIY build, Aarts Timers, StampOfApproval | ~$80–200 AUD | Most Versatile |

---

### Slide 9 — The upgrade path (don't make this feel required)
The key is framing: upgrades are optional, not mandatory.

```
Level 0: NTP only
  Clock: ±5ms typical | Camera: estimated delays | Cost: $0

Level 1: + GPS PPS receiver and GPS flasher
  Clock: <1ms | Camera: measured delays | Cost: +$50–80

Level 2: Shelyak TimeBox (Euro 155) or GPS NTP server (DIY or purchase)
  Off the shelf accurate PC time | Moderate cost | Similar workflow to NTP using SharpCap

Level 3: Dedicated occultation camera - Astrid, Analog camera + VTI, GPS enable camera
  Analog camera + VTI | Complex All-in-one solution | High cost | Complete different workflow from typical imaging
  Astrid| All-in-one solution | High cost | Completely different workflow from typical imaging 
  GPS Camera | All-in-one soluation | Very high cost | Similar workflow to NTP using SharpCap

```

**Key message:** *"Start at Level 0 today and learn how to do occultations. Upgrade later when you need to ."*

---

### Slide 10 — Real results (the strongest possible close)
**GPS PPS comparison results are available** from the GPS vs NTP Testing tool — internet NTP servers measured against GPS PPS ground truth. This is strong independent evidence and is potentially the most persuasive content in the talk. Export the UTC error chart before building this slide.

**Needed:** One or two examples of real NTP-timed occultation observations that produced good quality, accepted results. Ideally with:
- NTP accuracy summary for that session
- Camera delay applied
- Resulting chord/negative observation
- Report accepted by TTOA/IOTA

**If you don't have this yet:** Even a calibration run showing the end-to-end workflow (NTP monitor → camera delay measurement → Tangra extraction → uncertainty estimate) would work.

**Gap: This is the single biggest missing piece. Do you have real NTP-timed results to show?** No but I do have a 24 hour comparison of NTP running with a comparison to GPS PPS in `gps-timing-analysis\docs\gps-pps-comparison.png`, and a stability test against GPS flash timing `gps-timing-analysis\docs\gps-stability-test.png`

**Suggested structure for this slide without a real observation:**
Show the complete end-to-end chain for a hypothetical/practice session:
1. NTP Clock Accuracy tool — PIT offset estimate at the event time (e.g. −0.04ms ± 0.3ms)
2. GPS vs NTP Testing chart — server pool validated against GPS PPS ground truth
3. Camera delay (measured or estimated) with uncertainty
4. → Resulting total timing uncertainty in the report

This demonstrates the *workflow* is complete and traceable even without a specific accepted observation to point to. The chain is: UTC ← GPS PPS ← NTP servers ← NTP Clock Accuracy at PIT ← camera delay ← D/R timestamp.

---

### Slide 11 — Call to Action (different asks for different audiences)
Don't give one generic call to action. Address the room segments:

**For beginners and new observers:**
> "Download the installer and install NTP. Run it overnight. Check the NTP status tomorrow morning. If they look good enough you can do occultations."

**For experienced observers and community leaders:**
> "NTP is free, it works and the accuracy is verifiable and traceable to UTC. We should be recommending this as the starting point. Get your local club members doing occultations using NTP and help grow the observing community"

**For hardware developers:**
> "NTP timing grows the observer community. The upgrade path we've described ends with your products — and it starts here."

**For campaign coordinators:**
> "For large multi-station campaigns, NTP observers greatly expand chord coverage at zero hardware cost and is suitable for getting large observatories involved. We have the documentation. Let's get this listed formally."

**Concrete links:**
- NTP Installer: `github.com/labstercam/occultation-ntp-installer`
- Tools & documentation: `github.com/labstercam/occultation-tools`

---

## What Makes or Breaks This Talk

### Must-have (the single remaining critical gap)
1. **Real NTP monitor data** — a screenshot from an actual session showing delay ~3–8ms, jitter ~1–2ms, offset ±1–3ms on domestic fibre. Without this, Slide 3 is a claim, not evidence. This is priority 1.

### Available and confirmed
2. **The accuracy standard** — ANSWERED. Dave Herald (IOTA worldwide coordinator, 30+ years) has stated ~5ms is good enough; reliability and traceability matter most. He will be in the room. This closes the "what standard do we need to meet?" question definitively.
3. **GPS PPS comparison** — the GPS vs NTP Testing tool has results showing internet NTP servers within ±1–2ms of GPS PPS ground truth. Export/screenshot this for Slide 5 and Slide 10.
4. **Camera delay measurement and stability evidence** — `gps-timing-analysis/docs/gps-camera-calibration.png` (R²=0.990 calibration fit) and `gps-stability-test.png` (27,042 flashes, Std Dev 0.465ms over 9 hours) are available. These address the "how do you know the camera delay is stable and measurable?" objection with direct data.

### Still needed (lower priority)
5. **NTP Clock Accuracy loopstats chart** — for Slide 5 secondary visual. Shows long-term NTP offset stability from a real session.
6. **NTP offset field in an Occultation Manager report** — for Slide 4. Shows how the observation report documents NTP error at time of event, making traceability tangible.

### Strong existing content
- The installer story is excellent and very demonstrable
- The upgrade path concept is well-structured
- The tool set (NTP Clock Accuracy, GPS vs NTP Testing, Camera Timing Setup) is genuinely impressive and differentiating — most audiences won't know these exist

---

## Framing risk to avoid
The word **"beginner"** throughout risks anchoring the talk as "the second-best option for people who can't afford the real thing." Reframe throughout:
- "NTP is the **right** tool for most observations, not a compromise for beginners"
- "GPS cameras solve a problem most observers don't have yet"
- Most events do not require sub-1ms accuracy — NTP is fit for purpose, not inferior

---

## Assets Inventory

### Available now — all copied to `presentations/assets/`
| Asset | Filename | Use on |
|-------|----------|--------|
| Occultation path map (QLD/Brisbane/SI NZ) | `occultation-map.png` | Slide 1 — hook |
| Meinberg NTP Status, offset -0.035ms, Reach 377 | `ntp-server-monitor-status.png` | Slide 3 |
| NTP Clock Accuracy — Occultation Manager dialog, offset -0.380ms ±4.879ms (95%) at event PIT | `ntp-accuracy-example1.png` | Slides 5, 10 |
| NTP Clock Accuracy — full tool, PIT offset -0.2ms ±4.1ms, 4 charts | `ntp-accuracy-example2.png` | Slides 4, 5, 10 |
| Camera line delay calibration, R²=0.990 | `gps-camera-calibration.png` | Slide 7B |
| Long-term stability: 27,042 flashes, mean 7.377ms ±0.006ms (95% CI), 9 hours | `gps-stability-test.png` | Slides 7C, 10 |
| GPS PPS 24-hour NTP comparison | `gps-pps-comparison.png` | Slides 5, 10 |
| NTP installer screenshot | `NTP-Installer.png` | Slide 6 |
| Camera max-FPS coefficients | `camera-coefs.png` | Slide 7 |
| NTP Analyser (standalone tool) | `ntp-analyzer.png` | Slide 5 |
| NTP offset lifecycle diagram | `ntp-offset-lifecycle.svg` | Slides 3–4 |
| Dave Herald authority quote | Personal communication | Slide 4 — "~5ms good enough; traceability matters more" |

### Still needed before final Marp revision
| Asset | Priority | Notes |
|-------|----------|-------|
| ~~NTP Server Monitor screenshot~~ | ~~CRITICAL~~ | **RESOLVED** — `ntp-server-monitor-status.png` |
| ~~NTP Clock Accuracy PIT screenshot~~ | ~~High~~ | **RESOLVED** — `ntp-accuracy-example1.png` and `ntp-accuracy-example2.png` |
| ~~GPS vs NTP Testing UTC error chart~~ | ~~High~~ | **RESOLVED** — `gps-pps-comparison.png` |
| Occultation Manager report showing NTP offset field | Low | Slide 4 — shows traceability in an actual filed report |

---


