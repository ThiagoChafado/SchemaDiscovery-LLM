# scripts/prepare_data.py (versão com instruções)
import pandas as pd
import json
import os

# --- Configuration (aponte para seu subset) ---
DATASETS_DIR = 'datasets/subset_1GB'
MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest_subset.csv')
TRAINING_FILE_PATH = os.path.join(DATASETS_DIR, 'training_data.txt')
END_TOKEN = "<|endoftext|>" # O token de fim de texto ainda é útil

def createInstructionalFile():
    print("Starting data preparation with instructional format...")
    
    try:
        manifest = pd.read_csv(MANIFEST_PATH)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {MANIFEST_PATH}")
        return

    count = 0
    with open(TRAINING_FILE_PATH, 'w', encoding='utf-8') as training_file:
        for _, row in manifest.iterrows():
            jsonPath = row['json_path']
            schemaPath = row['schema_path']

            try:
                with open(jsonPath, 'r', encoding='utf-8') as f:
                    jsonContent = f.read()
                
                with open(schemaPath, 'r', encoding='utf-8') as f:
                    schemaContent = f.read()

                # --- NOVO FORMATO DE INSTRUÇÃO ---
                instruction = "INSTRUÇÃO: Gere o esquema para o JSON a seguir."
                json_header = "### JSON:"
                schema_header = "### Esquema:"

                formatted_string = (
                    f"{instruction}\n"
                    f"{json_header}\n{jsonContent}\n"
                    f"{schema_header}\n{schemaContent}{END_TOKEN}\n\n" # Adiciona duas quebras de linha para separar exemplos
                )
                
                training_file.write(formatted_string)
                count += 1
            except Exception as e:
                print(f"Error processing pair {jsonPath} / {schemaPath}: {e}")

    print(f"\nData preparation complete. Processed {count} pairs.")
    print(f"Instructional training data saved to: {TRAINING_FILE_PATH}")

if __name__ == '__main__':
    createInstructionalFile()