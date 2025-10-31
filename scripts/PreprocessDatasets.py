import os
import json
import ijson
from pathlib import Path

# --- Configurações ---
# O diretório onde estão seus arquivos JSON/JSONL originais.
INPUT_DIR = "datasets"

# O diretório base onde as pastas processadas (com os documentos) serão salvas.
OUTPUT_BASE_DIR = "processed"

# --- Configurações de Amostragem Inteligente ---
# 1. Defina o número máximo de documentos que você quer em sua subcoleção.
MAX_DOCUMENTS_PER_COLLECTION = 1000

# 2. Defina o tamanho máximo da subcoleção como uma PORCENTAGEM do tamanho do arquivo original.
#    Exemplo: 0.05 para 5%. Use 0 para ignorar o limite de tamanho.
MAX_SIZE_PERCENTAGE_PER_COLLECTION = 0.05

# 3. MODO DE AMOSTRAGEM: Define como os limites acima interagem.
#    'OR': Para quando o PRIMEIRO limite (documentos OU tamanho) for atingido. (Recomendado)
#    'AND': Para somente quando AMBOS os limites forem atingidos.
SAMPLING_MODE = 'OR'

# 4. AMOSTRAGEM ALEATÓRIA: Defina uma taxa para pegar 1 a cada N itens.
#    Use 1 para pegar todos os itens sequencialmente até atingir os limites.
#    Use 10 para pegar 1 item a cada 10, e assim por diante.
SAMPLING_RATE = 16
# --------------------

def sample_and_split_file(source_file, output_dir, max_docs, max_size_percentage, mode, rate):
    """
    Lê um arquivo JSON (array ou lines), faz a amostragem e divide em documentos individuais
    até que os limites configurados (número de docs, tamanho, modo) sejam satisfeitos.
    """
    # Calcula o tamanho alvo em bytes com base na porcentagem
    original_size_bytes = os.path.getsize(source_file)
    max_size_bytes = original_size_bytes * max_size_percentage if max_size_percentage > 0 else 0
    max_size_mb = max_size_bytes / (1024*1024)

    docs_output_dir = Path(output_dir) / "documents"
    docs_output_dir.mkdir(parents=True, exist_ok=True)
    
    docs_written = 0
    bytes_written = 0
    item_counter = 0
    
    try:
        file_format = None
        with open(source_file, 'r', encoding='utf-8') as f_peek:
            chunk = f_peek.read(100).strip()
            if chunk.startswith('['): file_format = 'json_array'
            elif chunk.startswith('{'): file_format = 'json_lines'
            else: print(f"  ERRO: Formato de arquivo desconhecido."); return

        source_iterator = None
        if file_format == 'json_array':
            f_in = open(source_file, "rb")
            source_iterator = ijson.items(f_in, 'item')
        elif file_format == 'json_lines':
            f_in = open(source_file, "r", encoding="utf-8")
            source_iterator = (json.loads(line) for line in f_in if line.strip())

        if not source_iterator: return

        print(f"  Iniciando amostragem com Modo='{mode}', Taxa=1/{rate}, Limites=(Docs={max_docs}, Tamanho={max_size_mb:.2f} MB)")
        
        for item in source_iterator:
            # Pula o item se não corresponder à taxa de amostragem
            if item_counter % rate != 0:
                item_counter += 1
                continue
            
            # --- LÓGICA DE PARADA INTELIGENTE ---
            docs_limit_reached = docs_written >= max_docs
            size_limit_reached = max_size_bytes > 0 and bytes_written >= max_size_bytes

            stop = False
            if mode == 'OR':
                if docs_limit_reached:
                    print(f"\n  Limite de {max_docs} documentos atingido. Parando.")
                    stop = True
                elif size_limit_reached:
                    print(f"\n  Limite de {max_size_mb:.2f} MB ({max_size_percentage * 100}%) atingido. Parando.")
                    stop = True
            elif mode == 'AND':
                # No modo 'AND', se um limite for desativado (ex: max_size_bytes=0), ele é considerado 'atingido'
                effective_size_limit = size_limit_reached if max_size_bytes > 0 else True
                if docs_limit_reached and effective_size_limit:
                    print(f"\n  Ambos os limites foram atingidos. Parando.")
                    stop = True
            
            if stop: break
            # --- FIM DA LÓGICA DE PARADA ---

            output_file_path = docs_output_dir / f"document_{docs_written + 1}.json"
            with open(output_file_path, "w", encoding="utf-8") as f_out:
                json.dump(item, f_out, ensure_ascii=False, indent=2)
            
            bytes_written += os.path.getsize(output_file_path)
            docs_written += 1
            item_counter += 1
            
            print(f"      -> Docs: {docs_written}/{max_docs} | Tamanho: {bytes_written / (1024*1024):.2f}/{max_size_mb:.2f} MB", end='\r')

        if 'f_in' in locals() and f_in:
            f_in.close()

    except Exception as e:
        print(f"\n  Ocorreu um erro durante o processamento de {source_file}: {e}")
    finally:
        print(f"\n  Processamento concluído. Total de {docs_written} documentos gerados ({bytes_written / (1024*1024):.2f} MB).")

def process_all_files(input_dir, output_base_dir, max_docs, max_size_percentage, mode, rate):
    Path(output_base_dir).mkdir(exist_ok=True)

    for file_name in os.listdir(input_dir):
        if not (file_name.endswith(".json") or file_name.endswith(".jsonl")): continue

        source_file_path = Path(input_dir) / file_name
        dataset_name = source_file_path.stem
        output_dir = Path(output_base_dir) / dataset_name
        
        print(f"\n--- Processando Dataset: {dataset_name} ({os.path.getsize(source_file_path)/(1024*1024):.2f} MB) ---")
        
        sample_and_split_file(source_file_path, output_dir, max_docs, max_size_percentage, mode, rate)

if __name__ == "__main__":
    process_all_files(
        INPUT_DIR,
        OUTPUT_BASE_DIR,
        MAX_DOCUMENTS_PER_COLLECTION,
        MAX_SIZE_PERCENTAGE_PER_COLLECTION,
        SAMPLING_MODE,
        SAMPLING_RATE
    )