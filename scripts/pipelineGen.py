# scripts/pipelineGen.py (VERSÃO FINAL com download seletivo e seguro)
import os
import shutil
from kaggle.api.kaggle_api_extended import KaggleApi
import math

# --- 1. CONFIGURAÇÃO ---

# Termos de busca mais amplos para encontrar mais fontes
SEARCH_TERMS = [
    "json api", "geojson", "json data", "configuration"
]
# Limite de datasets a serem inspecionados por termo de busca
DATASETS_PER_TERM = 20

# --- Filtro de Qualidade (Pré-Download) ---
# Tamanho máximo para um ARQUIVO JSON INDIVIDUAL que vamos baixar (em Megabytes).
# Este é o nosso principal filtro de segurança.
MAX_JSON_FILE_SIZE_MB = 2.0

# --- Configurações de Caminho ---
DATASETS_DIR = '../datasets/'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson/')
DOWNLOAD_LOG_PATH = os.path.join(DATASETS_DIR, 'dowloadLog.txt')


# --- 2. FUNÇÕES AUXILIARES ---

def loadProcessedDataLog():
    if not os.path.exists(DOWNLOAD_LOG_PATH): return set()
    with open(DOWNLOAD_LOG_PATH, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def logProcessedData(datasetRef):
    with open(DOWNLOAD_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{datasetRef}\n")

# --- 3. FUNÇÕES PRINCIPAIS (LÓGICA REESCRITA) ---

def find_and_download_good_jsons(api, datasetRef):
    """
    Inspeciona um dataset, lista seus arquivos e baixa seletivamente
    apenas os arquivos JSON pequenos e de alta qualidade.
    """
    print(f"\nInspecionando dataset: {datasetRef}...")
    try:
        # Pega a lista de arquivos DENTRO do dataset
        files_in_dataset = api.dataset_list_files(datasetRef).files
        
        keptFilesCount = 0
        max_file_size_bytes = MAX_JSON_FILE_SIZE_MB * 1024 * 1024

        for file_metadata in files_in_dataset:
            # O nome do arquivo está no atributo 'ref'
            filename = file_metadata.ref
            
            # Aplica os filtros ANTES de baixar
            if filename.endswith('.json') and file_metadata.totalBytes < max_file_size_bytes:
                print(f"  - Encontrado arquivo candidato: '{filename}' ({file_metadata.totalBytes / 1024:.1f} KB)")
                
                # Verifica se o arquivo já não existe localmente
                destinationPath = os.path.join(RAW_JSON_DIR, os.path.basename(filename))
                if not os.path.exists(destinationPath):
                    # Baixa o ARQUIVO INDIVIDUAL
                    api.dataset_download_file(datasetRef, filename, path=RAW_JSON_DIR)
                    print(f"    -> Baixado: Arquivo pequeno e de boa qualidade.")
                    keptFilesCount += 1
                else:
                    print(f"    -> Ignorado: Arquivo já existe.")

        if keptFilesCount > 0:
            print(f"  > Adicionados {keptFilesCount} novos arquivos deste dataset.")
            logProcessedData(datasetRef)
        else:
            print("  > Nenhum arquivo novo e de alta qualidade encontrado neste dataset.")
        return True

    except Exception as e:
        # Captura erros comuns, como datasets privados ou não encontrados (403/404)
        print(f"  > Erro ao inspecionar o dataset {datasetRef}: {e}. Pulando.")
        return False

def main():
    print("Initializing Kaggle API...")
    api = KaggleApi()
    api.authenticate()

    os.makedirs(RAW_JSON_DIR, exist_ok=True)
    processedDatasets = loadProcessedDataLog()
    
    # Busca por datasets primeiro
    all_datasets_to_inspect = []
    print("--- Fase 1: Buscando por datasets candidatos ---")
    for term in SEARCH_TERMS:
        print(f"Buscando por '{term}'...")
        try:
            # A busca é mais ampla, sem filtro de tamanho aqui
            datasets_list = api.dataset_list(search=term, sort_by='votes')
            # Limita a quantidade por termo para manter a busca rápida
            all_datasets_to_inspect.extend([d.ref for d in datasets_list[:DATASETS_PER_TERM]])
        except Exception as e:
            print(f"  > Erro durante a busca na API do Kaggle: {e}")

    # Remove duplicatas e datasets já processados
    unique_datasets = sorted(list(set(all_datasets_to_inspect)))
    datasets_to_process = [d for d in unique_datasets if d not in processedDatasets]
        
    if not datasets_to_process:
        print("\nNenhum dataset novo para inspecionar.")
        return
        
    print(f"\n--- Fase 2: Encontrados {len(datasets_to_process)} novos datasets para inspecionar e filtrar ---")
    for ref in datasets_to_process:
        find_and_download_good_jsons(api, ref)
        
    print("\n----------------------------------------------------")
    print("Aquisição de dados concluída.")

if __name__ == '__main__':
    main()