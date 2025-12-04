import json
import re
import os
import time

# --- KONFIGURATION ---
INPUT_FILENAME = "historical_ads_detailed_2022-11-30_to_2025-11-06.jsonl"
OUTPUT_FILENAME = "ai_ads_final_analysis_data.jsonl" # Nytt filnamn, nu JSONL
TEXT_KEY = 'description'
NESTED_TEXT_KEY = 'text'

# --- SÖKLISTA (Oförändrad) ---
keywords = [
    r"\bAI\b", r"\bML\b", r"\bNLP\b", r"\bLLM\b", 
    r"artificiell intelligens", r"maskininlärning", r"machine learning",
    r"deep learning", r"neurala nätverk", r"neural networks",
    r"computer vision", r"datorseende", r"natural language processing",
    r"generativ ai", r"generative ai", r"genai",
    r"språkmodell", r"language model", r"reinforcement learning",
    r"prediktiv analys", r"predictive analysis",
    r"chatgpt", r"openai", r"gpt-3", r"gpt-4", r"gpt-4o",
    r"copilot", r"midjourney", r"dall-e", r"stable diffusion",
    r"hugging face", r"pytorch", r"tensorflow", r"keras", 
    r"scikit-learn", r"langchain", r"gemini", r"anthropic", r"claude",
    r"bert", r"transformer model"
]
search_pattern = "|".join(keywords)

def main():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    input_path = os.path.join(desktop, INPUT_FILENAME)
    output_path = os.path.join(desktop, OUTPUT_FILENAME)

    print(f"--- Startar Fullständig Analys & Direkt JSONL-utskrift ---")
    print(f"Läser från fil: {input_path}")
    
    start_time = time.time()
    total_count = 0
    match_count = 0

    try:
        # Öppnar både input-filen (läsning) och output-filen (skrivning)
        with open(input_path, 'r', encoding='utf-8') as f_in, \
             open(output_path, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                total_count += 1
                
                if total_count % 20000 == 0:
                    print(f"--> Bearbetar rad {total_count}...")
                    
                try:
                    data = json.loads(line)
                    
                    headline = data.get('headline', '')
                    description_dict = data.get(TEXT_KEY, {})
                    ad_text = description_dict.get(NESTED_TEXT_KEY, '')
                    
                    if not ad_text:
                        continue
                    
                    searchable_text = (headline + ' ' + ad_text).lower()

                    if re.search(search_pattern, searchable_text):
                        match_count += 1
                        
                        matches = set(re.findall(search_pattern, searchable_text, flags=re.IGNORECASE))
                        match_keyword = ', '.join(matches)
                        
                        # --- SLUTGILTIGT JSON-OBJEKT ---
                        final_data = {
                            'id': data.get('id'),
                            'headline': headline,
                            'employer_name': data.get('employer_name'),
                            'publication_date': data.get('publication_date'),
                            'employment_type': data.get('employment_type'),
                            'municipality': data.get('municipality'),
                            'county': data.get('county'),
                            'region': data.get('region'),
                            'occupation_label': data.get('occupation_label'), # Inkluderad för analys
                            'match_keyword': match_keyword,
                            'full_description_text': ad_text # NU MED HELA TEXTEN
                        }
                        # Skriver JSON-objektet till filen följt av en ny rad
                        f_out.write(json.dumps(final_data) + '\n')
                        # -------------------------------

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        end_time = time.time()
        
        print(f"\n--- ANALYS KLAR ---")
        print(f"Total bearbetade rader: {total_count}")
        print(f"Hittade matchande annonser: {match_count}")
        print(f"Sparar fullständigt JSONL-resultat till: {output_path}")
        print(f"Total tid: {round(end_time - start_time, 2)} sekunder.")
        
    except FileNotFoundError:
        print(f"\nFEL: Hittade inte filen på sökvägen: {input_path}")
        return
    except Exception as e:
        print(f"\nFATALT FEL: Scriptet kraschade helt under filöppning/bearbetning. Fel: {e}")
        return

if __name__ == "__main__":
    main()
