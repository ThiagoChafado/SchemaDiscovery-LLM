

import pandas as pd
import json
import os


DATASETS_DIR = 'datasets/subset_1GB'
MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest_subset.csv')
TRAINING_FILE_PATH = os.path.join(DATASETS_DIR, 'training_data.txt')



JSON_START_TOKEN = "<|json|>"
SCHEMA_START_TOKEN = "<|schema|>"
END_TOKEN = "<|endoftext|>"

def createTrainingFile():
    print("Starting data preparation...")
    
    try:
        manifest = pd.read_csv(MANIFEST_PATH)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {MANIFEST_PATH}")
        print("Please run schemaGenerator.py first to create the manifest.")
        return

    count = 0
    with open(TRAINING_FILE_PATH, 'w', encoding='utf-8') as training_file:
        for _, row in manifest.iterrows():
            # Usa os caminhos completos diretamente do manifesto
            jsonPath = row['json_path']
            schemaPath = row['schema_path']

            try:
                if not os.path.exists(jsonPath):
                    print(f"File not found in manifest: {jsonPath}. Skipping pair.")
                    continue

                if not os.path.exists(schemaPath):
                    print(f"File not found in manifest: {schemaPath}. Skipping pair.")
                    continue

                with open(jsonPath, 'r', encoding='utf-8') as f:
                    jsonContent = f.read()
                
                with open(schemaPath, 'r', encoding='utf-8') as f:
                    schemaContent = f.read()

                formatted_string = (
                    f"{JSON_START_TOKEN}{jsonContent}"
                    f"{SCHEMA_START_TOKEN}{schemaContent}{END_TOKEN}\n"
                )
                
                training_file.write(formatted_string)
                count += 1
            except Exception as e:
                print(f"Error processing pair {jsonPath} / {schemaPath}: {e}")

    print(f"\nData preparation complete. Processed {count} pairs.")
    print(f"Training data saved to: {TRAINING_FILE_PATH}")

if __name__ == '__main__':
    createTrainingFile()