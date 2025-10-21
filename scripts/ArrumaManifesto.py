import os
import csv
from pathlib import Path
import shutil # Usado para a substituição segura do arquivo

# --- CONFIGURAÇÕES ---
MANIFEST_PATH = "manifest.csv"
# O diretório raiz onde os schemas gerados estão salvos
SCHEMA_DOCUMENTS_DIR = "processed/schema_documents/"
# ---------------------

def update_manifest_from_schemas():
    """
   ARRUMA A CAGADA QUE TINHA FEITO ANTES :P
    """
    print(f"Iniciando a verificação do manifesto '{MANIFEST_PATH}'...")
    
    # Define o caminho para um arquivo temporário
    temp_filepath = Path(MANIFEST_PATH).with_suffix('.csv.tmp')
    
    updated_count = 0
    processed_count = 0
    
    try:
        with open(MANIFEST_PATH, 'r', newline='', encoding='utf-8') as manifest_file, \
             open(temp_filepath, 'w', newline='', encoding='utf-8') as temp_file:
            
            # Usa a biblioteca CSV para ler e escrever de forma segura
            reader = csv.DictReader(manifest_file)
            # Garante que o writer use os mesmos cabeçalhos do leitor
            writer = csv.DictWriter(temp_file, fieldnames=reader.fieldnames)
            
            # Escreve o cabeçalho no arquivo temporário
            writer.writeheader()
            
            for row in reader:
                processed_count += 1
                # Verifica se o schema precisa ser checado
                if row.get("schema_generated", "false").strip().lower() == "false":
                    original_file_path = row["file"]
                    
                    # --- LÓGICA DE CAMINHO CORRIGIDA ---
                    # Reconstrói o caminho de saída exatamente como no script de geração
                    try:
                        p = Path(original_file_path)
                        dataset_name = p.parts[1] # ex: 'air-bnb-listings'
                        object_type = row["object_type"] # ex: 'documents'
                        base_name = p.name # ex: 'document_1.json'
                        
                        schema_file_path = Path(SCHEMA_DOCUMENTS_DIR) / dataset_name / object_type / base_name
                    except (IndexError, KeyError) as e:
                        print(f"\n Aviso: Linha com formato inesperado no manifesto. Pulando. Erro: {e}. Linha: {row}")
                        writer.writerow(row)
                        continue
                    # --- FIM DA CORREÇÃO ---
                    
                    # Se o arquivo de schema correspondente existir, atualiza a linha
                    if schema_file_path.exists():
                        row["schema_generated"] = "true"
                        updated_count += 1
                        print(f"   -> Atualizado: {base_name} do dataset '{dataset_name}'")
                
                # Escreve a linha (original ou modificada) no arquivo temporário
                writer.writerow(row)

    except FileNotFoundError:
        print(f" ERRO: O arquivo de manifesto não foi encontrado em '{MANIFEST_PATH}'")
        return
    except Exception as e:
        print(f" Ocorreu um erro inesperado durante o processamento: {e}")
        # Remove o arquivo temporário em caso de erro para não deixar lixo
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return

    # Se tudo correu bem, substitui o arquivo original pelo temporário
    # shutil.move é mais seguro para esta operação do que os.rename
    shutil.move(temp_filepath, MANIFEST_PATH)
    
    print("\n--- Relatório Final ---")
    print(f"Total de linhas processadas: {processed_count}")
    print(f"Entradas atualizadas para 'true': {updated_count}")
    print(f"Manifesto '{MANIFEST_PATH}' atualizado com sucesso!")


if __name__ == "__main__":
    update_manifest_from_schemas()