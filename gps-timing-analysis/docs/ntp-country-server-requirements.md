# Country-Specific NTP Server Requirements

This document tracks provider requirements for each country profile defined in `gps-timing-analysis/config/ntp-country-servers.json`.

Related inventory resource:
- `gps-timing-analysis/resources/national_utc_ntp_servers.json` (national UTC/NTP reference list, including usage notes and verification status).

Use this as an operational checklist before selecting or updating country server lists.

## national_utc_ntp_servers.json Field Reference

Use these conventions when updating `gps-timing-analysis/resources/national_utc_ntp_servers.json`.

Status values:
- `verified_public_hostname`: Public hostname(s) are explicitly known and listed in `ntp_servers`.
- `candidate_hostname_unverified`: Hostname(s) are plausible but not fully confirmed from authoritative source text in the current pass.
- `official_service_no_public_hostname`: Official service is confirmed but no public hostname is available.
- `no_public_server_found`: No publicly accessible server is currently known.

Group tags:
- `G20`: Country is in G20 scope for this inventory.
- `MajorEurope`: Country is tracked in the major-Europe subset.
- `Requested`: Country was explicitly requested for inclusion.
- `Alias`: Entry is a domain-code alias representation (for example `UK`).
- `Additional`: Country is outside base scope but intentionally included.

Optional field:
- `usage_note`: Add when policy/usage constraints matter (for example, server intended for upstream NTP servers only, or service not generally public).

## Australia (AU)

Profile in config:
- `AU` uses a tiered list:
  - Tier 1: NMI UTC(AUS) servers
  - Tier 2: Australian university public NTP servers
  - Tier 3: AU pool fallback (`au.pool.ntp.org` and `0..3.au.pool.ntp.org`)
- Server entries in this repository are configured with `iburst`.

Provider requirements and notes:
- NMI public endpoint:
  - `server ntp.nmi.gov.au iburst` (documented as public endpoint).
- NMI city-specific endpoints in this profile:
  - `server ntp.melbourne.nmi.gov.au iburst`
  - `server ntp.sydney.nmi.gov.au iburst`
  - `server ntp.sydney2.nmi.gov.au iburst`
  - `server ntp.perth.nmi.gov.au iburst`
  - `server ntp.adelaide.nmi.gov.au iburst`
  - `server ntp.brisbane.nmi.gov.au iburst`
- University public NTP endpoints in this profile (availability and access can vary):
  - `server ntp.unimelb.edu.au iburst` (University of Melbourne)
  - `server ntp.anu.edu.au iburst` (Australian National University)
  - `server ntp.adelaide.edu.au iburst` (University of Adelaide)
  - `server ntp.utas.edu.au iburst` (University of Tasmania)
  - `server ntp.monash.edu.au iburst` (Monash University)
  - `server ntp.curtin.edu.au iburst` (Curtin University)
- University server usage cautions:
  - acceptable use policy (AUP) may vary by university,
  - some servers may be inactive or unreachable at times,
  - do not override default polling settings,
  - this repository profile uses `iburst` on all configured server entries.
- AU pool fallback endpoints in this profile:
  - `server au.pool.ntp.org iburst`
  - `server 0.au.pool.ntp.org iburst`
  - `server 1.au.pool.ntp.org iburst`
  - `server 2.au.pool.ntp.org iburst`
  - `server 3.au.pool.ntp.org iburst`
- NMI access policy for traceable NTP services:
  - users must register their computer,
  - users must have a static IP address,
  - unregistered IPs may not be served for restricted service paths.
- Additional hostnames to verify before production use:
  - `ntp1.nmi.gov.au` (reported, existence not yet confirmed in this repo workflow)
  - `ntp2.nmi.gov.au` (reported, existence not yet confirmed in this repo workflow)
- Keep AU pool entries (`au.pool.ntp.org` and `0..3.au.pool.ntp.org`) as fallback diversity where policy allows.

Reference links:
- NMI time and frequency services:
  - `https://www.industry.gov.au/national-measurement-institute/nmi-services/physical-measurement-services/time-and-frequency-services`
- NMI guidance PDF (traceable NTP use):
  - `https://www.industry.gov.au/sites/default/files/2019-11/nmi-using-ntp-for-traceable-time-and-frequency.pdf`
- NMI service contact for registration:
  - `mailto:time@measurement.gov.au`
- NTP Pool AU zone:
  - `https://www.ntppool.org/zone/au`
- NTP Pool usage guidance:
  - `https://www.ntppool.org/en/use.html`

## New Zealand (NZ)

Profile in config:
- `NZ` uses `pool.msltime.measurement.govt.nz` and `s1..s4.ntp.net.nz`.
- Server entries in this repository are configured with `iburst`.

Provider requirements and notes:
- InternetNZ .nz NTP network (`ntp.net.nz`) usage policy applies to `s1..s4.ntp.net.nz` entries:
  - service is not public; intended for system administrators with systems normally based in NZ or Pacific Islands,
  - default OS poll intervals must not be overridden to poll more frequently,
  - equipment manufacturers/systems integrators must not ship products preconfigured to these servers,
  - desktop/laptop/home-router clients should use `s1..s4.ntp.net.nz`,
  - infrastructure clients (Stratum 2 servers, server-room equipment) should use `p1..p4.ntp.net.nz`,
  - consumer devices (printers, cameras, phones, etc.) must not be pointed directly at these servers.
- InternetNZ host naming and architecture notes:
  - backend servers are `ntp1..ntp4.ntp.net.nz`,
  - client hostnames `s1..s4` and `p1..p4` are CNAMEs used for policy/operational flexibility,
  - sites are in Albany, Auckland CBD, Wellington CBD, and Christchurch.
- Official MSL Stratum 1 pool endpoint:
  - `pool.msltime.measurement.govt.nz`
  - `161.65.172.9`
- Service scope and protocol behavior:
  - requests are geo-blocked to the NZ internet region,
  - servers respond to NTP/SNTP requests only,
  - servers do not respond to `datetime` requests.
- Capacity and architecture guidance from MSL:
  - limit direct access to three client machines,
  - point additional clients to local Stratum 2 relays.
- Registration status:
  - service is currently open-access,
  - serious users are strongly encouraged to register static IP(s) and contact email with MSL,
  - registered users receive service-change notifications.
- Naming and migration notes:
  - preferred names are `pool.msltime.measurement.govt.nz` or `161.65.172.9`,
  - `msltime.measurement.govt.nz` and `msltime1.measurement.govt.nz` continue as aliases,
  - legacy names `msltime.irl.cri.nz`, `msltime1.irl.cri.nz`, and `131.203.16.6` were discontinued.
- For additional NZ pool/community servers, follow NTP Pool usage guidance and avoid aggressive polling.

Reference links:
- InternetNZ .nz NTP network home:
  - `https://ntp.net.nz/`
- InternetNZ acceptable use policy (AUP):
  - `https://ntp.net.nz/pages/aup.html`
- InternetNZ network architecture:
  - `https://ntp.net.nz/pages/network-architecture.html`
- NZ official MSL NTP policy page:
  - `https://www.measurement.govt.nz/about-us/official-new-zealand-time/about-time`
- NZ official server hostname used in config:
  - `https://pool.msltime.measurement.govt.nz`
- MSL main site:
  - `https://www.measurement.govt.nz/`
- MSL contact page:
  - `https://www.measurement.govt.nz/contact-us`
- NTP Pool NZ zone:
  - `https://www.ntppool.org/zone/nz`
- NTP Pool usage guidance:
  - `https://www.ntppool.org/en/use.html`

## United States (US)

Profile in config:
- `US` uses mixed NIST site diversity plus US NTP Pool fallback:
  - `time.nist.gov`
  - `time-a-g.nist.gov`
  - `time-b-g.nist.gov`
  - `time-a-b.nist.gov`
  - `time-a-wwv.nist.gov`
  - `0.us.pool.ntp.org`
  - `1.us.pool.ntp.org`
- Server entries in this repository are configured with `iburst`.

Provider requirements and notes:
- Current US profile mixes a global NIST alias, explicit NIST East/West servers, and US pool fallback for resilience without manual reconfiguration.
- The two US pool entries are intentional fallback paths for observers whose network location has poor performance to NIST routes; advanced users can later replace pool entries with better-performing local servers based on `ntpq`/loopstats results.
- This repository uses explicit `server` lines and does not use the `pool` command.
- Operational tuning guidance for US deployments:
  - if measured offset/jitter is not stable enough, consider replacing part of the server set with more specific NIST hosts,
  - consider region- or city-appropriate servers where policy allows,
  - public university NTP servers may be useful in some regions, but verify availability and AUP before use,
  - monitor timing performance after each change and keep the set that gives the most consistent results for your location.
- Recommended process:
  - start with the default US profile in this repository,
  - collect loopstats/peerstats and review offset/jitter trends,
  - if performance is poor or inconsistent, rotate one or two upstream servers and re-test,
  - keep documented notes on which server mix performs best at your observing site.

Reference links:
- NIST Internet Time Service:
  - `https://www.nist.gov/pml/time-and-frequency-division/time-distribution/internet-time-service-its`
- NTP Pool US zone:
  - `https://www.ntppool.org/zone/us`

## Maintenance Notes

- Re-check provider requirements before each major release, since server access policies can change.
- Keep `gps-timing-analysis/config/ntp-country-servers.json` and this document in sync.
