#!/usr/bin/env python3
"""Build ntp_pool_zones.json from https://www.ntppool.org/.

This script fetches regional zone pages and extracts:
- regional pool hostnames and active IPv4/IPv6 counts,
- country pool hostnames and listed active counts,
- country -> region mapping.
"""

import datetime as _dt
import html as _html
import json
import os
import re
import urllib.request

BASE = "https://www.ntppool.org"
REGIONS = [
    ("africa", "Africa"),
    ("antarctica", "Antarctica"),
    ("asia", "Asia"),
    ("europe", "Europe"),
    ("north-america", "North America"),
    ("oceania", "Oceania"),
    ("south-america", "South America"),
]


def _fetch(path: str) -> str:
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "occultation-tools ntp-pool resource builder"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def _parse_zone_counts(html: str) -> dict:
    m4 = re.search(r"IPv4[\\s\\S]*?There are\\s+(\\d+)\\s+active servers in this zone\\.", html, re.I)
    m6 = re.search(r"IPv6[\\s\\S]*?There are\\s+(\\d+)\\s+active servers in this zone\\.", html, re.I)
    return {
        "ipv4_active": int(m4.group(1)) if m4 else None,
        "ipv6_active": int(m6.group(1)) if m6 else None,
    }


def _region_pool_hostnames(zone: str) -> list:
    return [
        "{}.pool.ntp.org".format(zone),
        "0.{}.pool.ntp.org".format(zone),
        "1.{}.pool.ntp.org".format(zone),
        "2.{}.pool.ntp.org".format(zone),
        "3.{}.pool.ntp.org".format(zone),
    ]


def _country_pool_hostnames(cc: str) -> list:
    return [
        "{}.pool.ntp.org".format(cc),
        "0.{}.pool.ntp.org".format(cc),
        "1.{}.pool.ntp.org".format(cc),
        "2.{}.pool.ntp.org".format(cc),
        "3.{}.pool.ntp.org".format(cc),
    ]


def _extract_countries_from_region_html(html: str) -> list:
    countries = []
    seen = set()

    # Primary parse: country link followed by pool hostname and listed count.
    primary_re = re.compile(
        r'<a[^>]+href=["\'](?:https?://www\.ntppool\.org)?(?:/[a-z]{2})?/zone/([a-z]{2})["\'][^>]*>'
        r'\s*([^<]+?)\s*</a>\s*(?:&mdash;|&#8212;|—|-)\s*[^()]*\((\d+)\)',
        re.I,
    )

    for match in primary_re.finditer(html):
        cc = match.group(1).lower()
        if cc in seen:
            continue
        seen.add(cc)
        countries.append(
            {
                "zone": cc,
                "name": re.sub(r"\s+", " ", _html.unescape(match.group(2))).strip(),
                "listed_active": int(match.group(3)),
            }
        )

    if countries:
        return countries

    # Fallback parse: find country links and scan nearby text for first count tuple.
    fallback_re = re.compile(
        r'<a[^>]+href=["\'](?:https?://www\.ntppool\.org)?(?:/[a-z]{2})?/zone/([a-z]{2})["\'][^>]*>'
        r'\s*([^<]+?)\s*</a>',
        re.I,
    )

    for match in fallback_re.finditer(html):
        cc = match.group(1).lower()
        if cc in seen:
            continue

        tail = html[match.end() : match.end() + 500]
        count_match = re.search(r"\((\d+)\)", tail)
        listed_active = int(count_match.group(1)) if count_match else None

        seen.add(cc)
        countries.append(
            {
                "zone": cc,
                "name": re.sub(r"\s+", " ", _html.unescape(match.group(2))).strip(),
                "listed_active": listed_active,
            }
        )

    return countries


def build() -> dict:
    regions_out = []
    country_map = {}

    for region_zone, region_name in REGIONS:
        html = _fetch("/zone/{}".format(region_zone))

        regions_out.append(
            {
                "zone": region_zone,
                "name": region_name,
                "pool_hostnames": _region_pool_hostnames(region_zone),
                "counts": _parse_zone_counts(html),
                "source_url": "{}/zone/{}".format(BASE, region_zone),
            }
        )

        for country in _extract_countries_from_region_html(html):
            cc = country["zone"]
            if cc in country_map:
                continue

            country_map[cc] = {
                "zone": cc,
                "name": country["name"],
                "region": region_zone,
                "region_name": region_name,
                "pool_hostnames": _country_pool_hostnames(cc),
                "counts": {
                    "listed_active": country["listed_active"],
                },
                "source_url": "{}/zone/{}".format(BASE, cc),
            }

    countries = [country_map[k] for k in sorted(country_map)]
    country_to_region = {c["zone"]: c["region"] for c in countries}

    return {
        "generated_at_utc": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": BASE + "/",
        "notes": [
            "Region counts are parsed from each regional zone page.",
            "Country listed_active counts are parsed from regional zone pages.",
            "Pool hostnames include base zone plus 0..3 aliases.",
        ],
        "regions": regions_out,
        "countries": countries,
        "country_to_region": country_to_region,
    }


def main() -> None:
    data = build()
    out_path = os.path.join(os.path.dirname(__file__), "ntp_pool_zones.json")
    with open(out_path, "w", encoding="ascii") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("Wrote {}".format(out_path))
    print("regions={} countries={}".format(len(data["regions"]), len(data["countries"])))


if __name__ == "__main__":
    main()
