import os
import json
import pandas as pd

# --- Configuration ---
DATASETS_DIR = 'datasets'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson')
CLEANED_JSON_DIR = os.path.join(DATASETS_DIR, 'cleanedJson') # <-- Nova pasta de saída
MASTER_MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest.csv')
CLEANED_MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest_cleaned.csv') # <-- Novo manifesto

# Se uma string for maior que este valor, ela será cortada.
MAX_STRING_LENGTH = 200

def truncate_long_strings(data):
    """
    Função recursiva para percorrer um objeto JSON e encurtar strings longas.
    """
    if isinstance(data, dict):
        return {k: truncate_long_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [truncate_long_strings(item) for item in data]
    elif isinstance(data, str) and len(data) > MAX_STRING_LENGTH:
        return data[:MAX_STRING_LENGTH] + "..."
    else:
        return data

def clean_and_format_json_files():
    """
    Lê os arquivos JSON brutos, os limpa e formata, salvando-os
    em um novo diretório e criando um novo manifesto.
    """
    print("--- Iniciando Limpeza e Formatação dos Dados ---")
    os.makedirs(CLEANED_JSON_DIR, exist_ok=True)
    
    try:
        manifest = pd.read_csv(MASTER_MANIFEST_PATH)
    except FileNotFoundError:
        print(f"ERRO: Manifesto principal '{MASTER_MANIFEST_PATH}' não encontrado.")
        print("Execute o schemaGenerator.py primeiro.")
        return

    cleaned_pairs = []
    total_files = len(manifest)

    for i, row in manifest.iterrows():
        json_filename = os.path.basename(row['json_path'])
        source_path = row['json_path']
        dest_path = os.path.join(CLEANED_JSON_DIR, json_filename)
        
        print(f"Processando [{i+1}/{total_files}]: {json_filename}")

        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Aplica a limpeza para encurtar strings longas
            cleaned_data = truncate_long_strings(json_data)
            
            # Salva o arquivo limpo e formatado (pretty-printed)
            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=4)
            
            # Adiciona o par limpo ao novo manifesto
            cleaned_pairs.append({
                'json_path': dest_path,
                'schema_path': row['schema_path']
            })

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  -> AVISO: Não foi possível processar o arquivo {json_filename}. Pulando. Erro: {e}")
            
    # Salva o novo manifesto que aponta para os arquivos limpos
    try:
        df = pd.DataFrame(cleaned_pairs)
        df.to_csv(CLEANED_MANIFEST_PATH, index=False)
        print(f"\n[SUCESSO] Limpeza concluída. {len(cleaned_pairs)} arquivos limpos.")
        print(f"Novo manifesto salvo em: {CLEANED_MANIFEST_PATH}")
    except Exception as e:
        print(f"ERRO ao salvar o novo manifesto: {e}")


if __name__ == '__main__':
    clean_and_format_json_files()