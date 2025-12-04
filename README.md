# AI-trender i Sverige 2022–2025 – Jobbannonser från Platsbanken

Detta repo innehåller den kod jag använt för att analysera hur AI-kompetens
efterfrågas i svenska jobbannonser 2022–2025.

Projektet bygger på data från Arbetsförmedlingens öppna API via Jobtech Dev
och ligger till grund för min artikel och Looker Studio-rapport om
AI-trender i Sverige.

## Översikt

Pipeline i två steg:

1. **Hämta historiska annonser** från Platsbankens `historical`-API  
   (`src/fetch_historical_detailed.py`)

2. **Filtrera fram AI-relaterade annonser** med hjälp av sökord / regex  
   (`src/filter_ai_ads.py`)

Ut kommer en JSONL-fil med de jobbannonser där annonsen innehåller AI-relaterade
kompetenser (AI, machine learning, LLM, generative AI m.m.) som jag sedan
läst in i BigQuery och visualiserat i Looker Studio.

## Kom igång

Klona repot och skapa en virtuell miljö (frivilligt men rekommenderas):

```bash
git clone https://github.com/<ditt-användarnamn>/ai-trender-sverige-jobbannonser.git
cd ai-trender-sverige-jobbannonser

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
