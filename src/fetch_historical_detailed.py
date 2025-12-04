import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://historical.api.jobtechdev.se/search"
HEADERS = {
    "User-Agent": "ai-platsbanken-mats-lindholm/1.0",
    "Accept": "application/json",
}

# Historikperiod
# START: ChatGPT-lansering (2022-11-30)
# SLUT: Dagen innan din dagliga hämtning (2025-11-06)
START_DATE = datetime(2022, 11, 30)
END_DATE = datetime(2025, 11, 6)

LIMIT = 100
MAX_OFFSET = 2000
SLEEP_SECONDS = 0.2
MAX_RETRIES = 3

# Yrkesområden du är extra intresserad av (logg, inte filter längre!)
TARGET_SSYK4 = {
    "2431", "2433", "2511", "2512", "2513", "2519",
    "2521", "2522", "2523", "2621",
}


def extract_ssyk4(ad: dict):
    """
    Hämta SSYK4 ur occupation.legacy_ams_taxonomy_id (historical API),
    fallback till occupation.ssyk om det skulle finnas.
    """
    occ = ad.get("occupation")

    if isinstance(occ, dict):
        code = occ.get("legacy_ams_taxonomy_id") or occ.get("ssyk")
        if code:
            return str(code)[:4]

    if isinstance(occ, list) and occ:
        first = occ[0]
        if isinstance(first, dict):
            code = first.get("legacy_ams_taxonomy_id") or first.get("ssyk")
            if code:
                return str(code)[:4]

    return None


def normalize(ad: dict) -> dict:
    """
    Normalisera och inkluderar alla viktiga fält (description, must_have, nice_to_have, etc.) 
    som STRUCT/RECORD för djup analys. Använder .get() för robusthet.
    """
    ssyk4 = extract_ssyk4(ad)

    # Plocka ut de komplexa fälten i sin helhet, returnerar None om de saknas
    description_data = ad.get("description")
    occupation_data = ad.get("occupation")
    must_have_data = ad.get("must_have")
    nice_to_have_data = ad.get("nice_to_have")

    return {
        "id": ad.get("id"),
        "external_id": ad.get("external_id"),
        "headline": ad.get("headline"),
        # Använder .get() för nästlade fält för extra säkerhet
        "employer_name": (ad.get("employer") or {}).get("name"), 
        "publication_date": ad.get("publication_date") or ad.get("published"),
        "last_publication_date": ad.get("last_publication_date"),
        "application_deadline": ad.get("application_deadline"),
        
        # **** VIKTIGA FÄLT FÖR DJUP ANALYS (STRUCTS/RECORDS) ****
        "description": description_data,        # KRITISKT! Innehåller texten och text_formatted
        "must_have": must_have_data,            # Obligatoriska skills, utbildning, etc.
        "nice_to_have": nice_to_have_data,      # Önskvärda skills, utbildning, etc.
        "occupation": occupation_data,          # Yrkesklassificering
        "salary_type": ad.get("salary_type"),
        "duration": ad.get("duration"),
        "salary_description": ad.get("salary_description"),
        # *****************************************
        
        "workplace_address": ad.get("workplace_address"),
        "employment_type": ad.get("employment_type"),
        "working_hours_type": ad.get("working_hours_type"),
        "source_type": ad.get("source_type") or "historical_api",
        "ssyk4": ssyk4,
    }


def fetch_chunk(day: datetime, fh) -> tuple[int, int]:
    """
    Hämta alla annonser för en dag, med retry och offset-hantering.
    SKRIVER NU ALLA ANNONSER (normaliserade) – INGEN FILTRERING.
    """
    day_start = day.strftime("%Y-%m-%dT00:00:00")
    day_end = day.strftime("%Y-%m-%dT23:59:59")

    total_ads = 0
    total_in_target = 0
    offset = 0

    while True:
        if offset > MAX_OFFSET:
            print(f"  [VARNING] Nått max offset {MAX_OFFSET} för {day.date()} – risk att missa annonser.")
            break

        params = {
            "published-after": day_start,
            "published-before": day_end,
            "limit": LIMIT,
            "offset": offset,
        }

        # Retry-logik
        resp = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Höjer timeout för större säkerhet
                resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=120) 
                resp.raise_for_status()
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                print(f"⚠️ {type(e).__name__} vid offset={offset} (försök {attempt}/{MAX_RETRIES}) – väntar 10s...")
                time.sleep(10)
        if resp is None:
            print(f"❌ Misslyckades efter {MAX_RETRIES} försök på offset={offset}. Hoppar över återstoden av {day.date()}.")
            break

        data = resp.json()
        hits = data.get("hits") or data.get("results") or []
        if not hits:
            break

        batch_in_target = 0
        for ad in hits:
            total_ads += 1

            norm = normalize(ad)
            fh.write(json.dumps(norm, ensure_ascii=False) + "\n")

            # bara logg: hur många hör till dina SSYK-koder
            if norm["ssyk4"] in TARGET_SSYK4:
                total_in_target += 1
                batch_in_target += 1

        print(f"  offset={offset}: {len(hits)} träffar, {batch_in_target} i TARGET_SSYK4, totalt {total_ads} annonser")

        if len(hits) < LIMIT:
            # sista sidan för dagen
            break

        offset += LIMIT
        time.sleep(SLEEP_SECONDS)

    print(f"  -> Klar dag {day.date()}: {total_ads} annonser, varav {total_in_target} i TARGET_SSYK4.\n")
    return total_ads, total_in_target


def main():
    # Nytt filnamn för den detaljerade historiken
    output_file = f"historical_ads_detailed_{START_DATE.date()}_to_{END_DATE.date()}.jsonl"
    total_all_ads = 0
    total_all_in_target = 0
    current = START_DATE

    # Använder 'w' (write) för att starta en ny fil
    with open(output_file, "w", encoding="utf-8") as fh: 
        while current.date() <= END_DATE.date():
            print(f"Dag: {current.date()}")
            day_total, day_in_target = fetch_chunk(current, fh)
            total_all_ads += day_total
            total_all_in_target += day_in_target
            fh.flush()
            current += timedelta(days=1)
            time.sleep(0.5)

    print(f"\nKLART.")
    print(f"Totalt antal annonser från {START_DATE.date()} till {END_DATE.date()}: {total_all_ads}")
    print(f"Varav med SSYK4 i TARGET_SSYK4: {total_all_in_target}")
    print(f"Fil skapad: {output_file}")


if __name__ == "__main__":
    main()
