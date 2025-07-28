# scripts/create_subset.py
import os
import pandas as pd
import shutil
import random
import csv

DATASETS_DIR = 'datasets'
# Onde estão os dados originais
MASTER_MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest_cleaned.csv')
# Onde o novo subconjunto será salvo
SUBSET_DIR = os.path.join(DATASETS_DIR, 'subset_1GB')
SUBSET_RAW_JSON_DIR = os.path.join(SUBSET_DIR, 'rawJson')
SUBSET_PROCESSED_SCHEMAS_DIR = os.path.join(SUBSET_DIR, 'processedSchemas')
SUBSET_MANIFEST_PATH = os.path.join(SUBSET_DIR, 'manifest_subset.csv')

# Tamanho alvo para o nosso subconjunto de dados (em Gigabytes)
TARGET_SIZE_GB = 0.5

def create_dataset_subset():
    """
    Creates a random subset of the full dataset to make training feasible
    on memory-constrained hardware.
    """
    print(f"Creating a dataset subset of approximately {TARGET_SIZE_GB} GB...")

    # 1. Crie as pastas de destino
    os.makedirs(SUBSET_RAW_JSON_DIR, exist_ok=True)
    os.makedirs(SUBSET_PROCESSED_SCHEMAS_DIR, exist_ok=True)

    # 2. Leia o manifesto principal
    try:
        manifest = pd.read_csv(MASTER_MANIFEST_PATH)
    except FileNotFoundError:
        print(f"Error: Master manifest not found at {MASTER_MANIFEST_PATH}")
        return

    # 3. Embaralhe a lista de arquivos para garantir uma amostra aleatória
    file_pairs = manifest.to_dict('records')
    random.shuffle(file_pairs)

    new_manifest_data = []
    current_size_gb = 0.0

    # 4. Copie os arquivos até atingir o tamanho alvo
    for pair in file_pairs:
        if current_size_gb >= TARGET_SIZE_GB:
            break

        source_json_path = pair['json_path']
        source_schema_path = pair['schema_path']

        # Pega apenas o nome do arquivo para criar o caminho de destino
        json_filename = os.path.basename(source_json_path)
        schema_filename = os.path.basename(source_schema_path)

        dest_json_path = os.path.join(SUBSET_RAW_JSON_DIR, json_filename)
        dest_schema_path = os.path.join(SUBSET_PROCESSED_SCHEMAS_DIR, schema_filename)

        try:
            # Copia o arquivo JSON e o Schema
            shutil.copyfile(source_json_path, dest_json_path)
            shutil.copyfile(source_schema_path, dest_schema_path)
            
            # Adiciona o tamanho do arquivo JSON à contagem atual
            current_size_gb += os.path.getsize(dest_json_path) / (1024**3)

            # Adiciona o novo par ao novo manifesto
            new_manifest_data.append({
                'json_path': dest_json_path,
                'schema_path': dest_schema_path
            })
            print(f"Copied '{json_filename}'. Current size: {current_size_gb:.2f} GB")

        except Exception as e:
            print(f"Could not copy pair for {json_filename}. Error: {e}")

    # 5. Crie o novo arquivo de manifesto para o subconjunto
    try:
        with open(SUBSET_MANIFEST_PATH, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['json_path', 'schema_path']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_manifest_data)
        print(f"\nSubset manifest created at {SUBSET_MANIFEST_PATH} with {len(new_manifest_data)} pairs.")
        print(f"Final subset size: {current_size_gb:.2f} GB")
    except Exception as e:
        print(f"Error writing subset manifest: {e}")

if __name__ == '__main__':
    create_dataset_subset()