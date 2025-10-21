import os
import json
import csv
from pathlib import Path
from collections import defaultdict
import genson # A biblioteca que fará o trabalho pesado

# --- CONFIGURAÇÕES ---
MANIFEST_PATH = "manifest.csv"

# O diretório onde os schemas mestres gerados por este método serão salvos.
SCHEMA_OUTPUT_DIR = "traditional_schemas/"
# ---------------------


def load_approved_files_from_manifest(manifest_path):
    """
    Lê o manifesto e retorna um dicionário agrupando os caminhos dos arquivos
    marcados com 'schema_generated' = 'true' por dataset.
    
    Returns:
        dict: Um dicionário como {'dataset_name': ['path/to/file1.json', ...]}
    """
    approved_files = defaultdict(list)
    print(f" Lendo o manifesto '{manifest_path}' para encontrar arquivos aprovados...")
    
    try:
        with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Verifica se o schema foi gerado com sucesso
                if row.get("schema_generated", "false").strip().lower() == "true":
                    file_path = row["file"]
                    try:
                        # Extrai o nome do dataset do caminho do arquivo
                        # Assumindo a estrutura: 'processed/DATASET_NAME/...'
                        dataset_name = Path(file_path).parts[1]
                        approved_files[dataset_name].append(file_path)
                    except IndexError:
                        print(f"   ->   Aviso: Formato de caminho inválido no manifesto, pulando: {file_path}")
    except FileNotFoundError:
        print(f"   ->  ERRO: Arquivo de manifesto não encontrado em '{manifest_path}'. Nenhum arquivo será processado.")
        return {}
        
    print(f"   -> Encontrados arquivos aprovados para {len(approved_files)} datasets.")
    return approved_files


def generate_master_schema_for_directory(json_file_paths):
    """
    Usa a biblioteca 'genson' para gerar um único schema a partir de uma lista de arquivos JSON.
    """
    builder = genson.SchemaBuilder()
    total_files = len(json_file_paths)
    
    for i, file_path in enumerate(json_file_paths):
        print(f"      -> Lendo arquivo ({i+1}/{total_files}): {os.path.basename(file_path)}", end='\r')
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                builder.add_object(data)
        except FileNotFoundError:
            print(f"\n       Aviso: Arquivo listado no manifesto não foi encontrado no disco: {file_path}")
        except json.JSONDecodeError:
            print(f"\n        Aviso: JSON inválido pulado: {file_path}")
        except Exception as e:
            print(f"\n       Erro inesperado ao ler o arquivo {file_path}: {e}")
            
    print(f"\n      -> Geração do schema concluída para {total_files} arquivos.")
    return builder.to_schema()


def main():
    """
    Gera um schema mestre tradicional para cada dataset, usando apenas os arquivos
    marcados como 'true' no manifesto.
    """
    # Garante que o diretório de saída exista
    os.makedirs(SCHEMA_OUTPUT_DIR, exist_ok=True)
    
    # Carrega a lista de arquivos a serem processados a partir do manifesto
    approved_files_by_dataset = load_approved_files_from_manifest(MANIFEST_PATH)

    if not approved_files_by_dataset:
        print("\nNenhum arquivo aprovado encontrado. Encerrando o processo.")
        return
        
    print("\nIniciando a geração de schemas tradicionais...")
    
    for dataset_name, file_list in approved_files_by_dataset.items():
        print(f"\n--- Processando o dataset: {dataset_name} ---")
        
        if not file_list:
            print("   -> Nenhum arquivo aprovado para este dataset. Pulando.")
            continue
            
        print(f"   -> Encontrados {len(file_list)} arquivos aprovados. Gerando o schema mestre...")
        
        # Gera o schema mestre usando a lista de arquivos filtrada
        master_schema = generate_master_schema_for_directory(file_list)
        
        output_filename = f"{dataset_name}_traditional_schema.json"
        output_path = os.path.join(SCHEMA_OUTPUT_DIR, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(master_schema, f, indent=2, ensure_ascii=False)
            print(f"   ->  Schema mestre salvo com sucesso em: '{output_path}'")
        except Exception as e:
            print(f"\n   ->  Erro ao salvar o arquivo final para '{dataset_name}': {e}")
        
    print("\n--- Processo Finalizado ---")

if __name__ == "__main__":
    main()