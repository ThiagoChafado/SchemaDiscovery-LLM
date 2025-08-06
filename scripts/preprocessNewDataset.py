# scripts/preprocess_colleague_data.py
import os
import json
import pandas as pd
import shutil

# --- Configuração ---

# Pasta de entrada com os dados do seu colega
COLLEAGUE_SCHEMAS_DIR = 'newDataset/schemas'
COLLEAGUE_DOCS_DIR = 'newDataset/documents'

# Pasta de saída, onde os dados serão preparados para o seu pipeline
OUTPUT_DIR = 'datasets/preprocessed_colleague_data'
OUTPUT_RAW_JSON_DIR = os.path.join(OUTPUT_DIR, 'rawJson')
OUTPUT_SCHEMAS_DIR = os.path.join(OUTPUT_DIR, 'processedSchemas')
OUTPUT_MANIFEST_PATH = os.path.join(OUTPUT_DIR, 'manifest.csv')

def preprocess_colleague_data():
    """
    Lê o dataset do colega (múltiplos docs por arquivo), desmembra em arquivos
    individuais e cria um manifest.csv compatível com o pipeline de treinamento.
    """
    print("--- Iniciando pré-processamento do dataset do colega ---")
    
    # 1. Cria as pastas de saída
    os.makedirs(OUTPUT_RAW_JSON_DIR, exist_ok=True)
    os.makedirs(OUTPUT_SCHEMAS_DIR, exist_ok=True)
    
    if not os.path.exists(COLLEAGUE_SCHEMAS_DIR):
        print(f"ERRO: Pasta de esquemas de entrada não encontrada em '{COLLEAGUE_SCHEMAS_DIR}'")
        return

    # Lista todos os esquemas antes de começar
    all_schema_files = [f for f in os.listdir(COLLEAGUE_SCHEMAS_DIR) if f.endswith('.schema.json')]
    print(f"Encontrados {len(all_schema_files)} arquivos de esquema para processar: {all_schema_files}")

    manifest_data = []
    
    # 2. Itera sobre cada arquivo de ESQUEMA na lista
    for schema_filename in all_schema_files:
        print(f"\n--- INICIANDO PROCESSAMENTO PARA: {schema_filename} ---")
        
        schema_base_name = schema_filename.replace('.schema.json', '')
        
        # Copia o arquivo de esquema para a nossa pasta de saída
        source_schema_path = os.path.join(COLLEAGUE_SCHEMAS_DIR, schema_filename)
        dest_schema_path = os.path.join(OUTPUT_SCHEMAS_DIR, schema_filename)
        shutil.copyfile(source_schema_path, dest_schema_path)
        
        # Encontra e processa o arquivo de DOCUMENTOS correspondente
        doc_filename = f"{schema_base_name}.json"
        doc_filepath = os.path.join(COLLEAGUE_DOCS_DIR, doc_filename)

        if not os.path.exists(doc_filepath):
            print(f"  -> AVISO: Arquivo de documentos '{doc_filename}' não encontrado. Pulando.")
            continue # Pula para o próximo schema_filename no loop
            
        try:
            with open(doc_filepath, 'r', encoding='utf-8') as f:
                # Assumimos que o arquivo contém um array de documentos JSON
                documents = json.load(f)
            
            if not isinstance(documents, list):
                print(f"  -> AVISO: O arquivo '{doc_filename}' não contém um array JSON. Pulando.")
                continue

            print(f"  -> Encontrados {len(documents)} documentos. Desmembrando e salvando arquivos individuais...")
            
            # 5. Desmembra cada documento em um arquivo individual
            for i, doc in enumerate(documents):
                instance_filename = f"{schema_base_name}_instance_{i+1}.json"
                instance_filepath = os.path.join(OUTPUT_RAW_JSON_DIR, instance_filename)
                
                with open(instance_filepath, 'w', encoding='utf-8') as f_out:
                    json.dump(doc, f_out, indent=4)
                    
                # Adiciona a entrada ao nosso manifesto
                manifest_data.append({
                    'json_path': instance_filepath,
                    'schema_path': dest_schema_path
                })
            
            print(f"  -> {len(documents)} arquivos individuais salvos com sucesso.")
            
        except Exception as e:
            print(f"  -> ERRO ao processar o arquivo de documentos '{doc_filename}': {e}")

        print(f"--- PROCESSAMENTO CONCLUÍDO PARA: {schema_filename} ---")

    # 6. Salva o arquivo de manifesto final
    if not manifest_data:
        print("\nNenhum dado foi processado. O manifesto não foi criado.")
        return
        
    try:
        df = pd.DataFrame(manifest_data)
        df.to_csv(OUTPUT_MANIFEST_PATH, index=False)
        print(f"\n[SUCESSO] Pré-processamento concluído.")
        print(f"Foram criados {len(manifest_data)} arquivos JSON individuais no total.")
        print(f"Novo manifesto salvo em: {OUTPUT_MANIFEST_PATH}")
    except Exception as e:
        print(f"\nERRO ao salvar o manifesto: {e}")

if __name__ == '__main__':
    # Instala o pandas se não estiver presente
    try:
        import pandas
    except ImportError:
        import subprocess, sys
        print("Instalando a biblioteca 'pandas'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    
    preprocess_colleague_data()