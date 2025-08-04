# scripts/pipelineGen.py (VERSÃO FINAL com API do Kaggle)
import os
import shutil
from kaggle.api.kaggle_api_extended import KaggleApi # <-- NOVO IMPORT
import math

# --- Configuration ---
# ... (sem alterações nesta seção) ...
DATASETS_DIR = '../datasets/'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson/')
TEMP_DOWNLOADS_DIR = os.path.join(DATASETS_DIR, 'tempDowloads/')
DOWNLOAD_LOG_PATH = os.path.join(DATASETS_DIR, 'dowloadLog.txt')
SEARCH_TERMS = [
    "government json api", "scientific data json", "product catalog json",
    "financial data json", "nested json", "geolocation json"
]
DATASETS_PER_TERM = 5
MAX_DATASET_SIZE_MB = 200

# --- Funções (sem alterações aqui) ---
def loadProcessedDataLog():
    if not os.path.exists(DOWNLOAD_LOG_PATH): return set()
    with open(DOWNLOAD_LOG_PATH, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def logProcessedData(datasetRef):
    with open(DOWNLOAD_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{datasetRef}\n")

# --- FUNÇÕES REESCRITAS COM A API ---

def searchKaggleDatasets(api, searchTerm, sizeLimitMb):
    print(f"\nSearching for datasets matching '{searchTerm}' (smaller than {sizeLimitMb}MB)...")
    try:
        # Usa a função da API para listar datasets
        datasets_list = api.dataset_list(search=searchTerm)
        
        filteredRefs = []
        for dataset in datasets_list:
            # A API retorna o tamanho em bytes. Convertemos para MB.
            sizeMb = dataset.totalBytes / (1024 * 1024) if dataset.totalBytes else 0
            if sizeMb <= sizeLimitMb:
                # O atributo 'ref' contém a referência, como 'username/slug'
                filteredRefs.append(dataset.ref)
        
        print(f"  > Found {len(filteredRefs)} datasets under the size limit.")
        return filteredRefs
        
    except Exception as e:
        print(f"  > Error during Kaggle API search: {e}")
        return []

def downloadAndProcessDataset(api, datasetRef):
    print(f"\nProcessing dataset: {datasetRef}...")
    if os.path.exists(TEMP_DOWNLOADS_DIR): shutil.rmtree(TEMP_DOWNLOADS_DIR)
    os.makedirs(TEMP_DOWNLOADS_DIR)
    
    try:
        # Usa a função da API para baixar e descompactar os arquivos
        api.dataset_download_files(datasetRef, path=TEMP_DOWNLOADS_DIR, unzip=True)
        
        print(f"  > Download and unzip successful for {datasetRef}.")
        movedFilesCount = 0
        for root, _, files in os.walk(TEMP_DOWNLOADS_DIR):
            for name in files:
                if name.endswith('.json'):
                    sourcePath = os.path.join(root, name)
                    destinationPath = os.path.join(RAW_JSON_DIR, name)
                    if not os.path.exists(destinationPath):
                        shutil.move(sourcePath, destinationPath)
                        movedFilesCount += 1
                    else:
                        print(f"  - File '{name}' already exists. Skipping.")
        if movedFilesCount > 0:
            print(f"  > Moved {movedFilesCount} new .json file(s) to '{RAW_JSON_DIR}'.")
            logProcessedData(datasetRef)
        else:
            print("  > No new JSON files found to move.")
    except Exception as e:
        print(f"  > Error downloading dataset {datasetRef}: {e}")
    finally:
        if os.path.exists(TEMP_DOWNLOADS_DIR): shutil.rmtree(TEMP_DOWNLOADS_DIR)

def main():
    # --- NOVO: Inicialização da API ---
    print("Initializing Kaggle API...")
    api = KaggleApi()
    api.authenticate() # Autentica usando o arquivo ~/.kaggle/kaggle.json
    print("Kaggle API authenticated successfully.")

    os.makedirs(RAW_JSON_DIR, exist_ok=True)
    processedDatasets = loadProcessedDataLog()
    print(f"Found {len(processedDatasets)} previously processed datasets in the log.")
    
    allNewDatasetsToProcess = []
    for term in SEARCH_TERMS:
        # Passa o objeto 'api' para a função de busca
        datasetRefs = searchKaggleDatasets(api, term, MAX_DATASET_SIZE_MB)
        newRefsForTerm = 0
        for ref in datasetRefs:
            if newRefsForTerm >= DATASETS_PER_TERM: break
            if ref not in processedDatasets and ref not in allNewDatasetsToProcess:
                allNewDatasetsToProcess.append(ref)
                newRefsForTerm += 1
                
    if not allNewDatasetsToProcess:
        print("\nNo new datasets to download based on the specified criteria. Exiting.")
        return
        
    print(f"\nFound a total of {len(allNewDatasetsToProcess)} new, unique datasets to process.")
    for ref in allNewDatasetsToProcess:
        # Passa o objeto 'api' para a função de download
        downloadAndProcessDataset(api, ref)
        
    print("\n----------------------------------------------------")
    print("Data acquisition phase complete.")

if __name__ == '__main__':
    main()
