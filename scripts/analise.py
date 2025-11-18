import os
import json
import csv
import ijson
from collections import deque

# --- CONFIGURAÇÕES ---
ORIGINAL_DATA_DIR = "datasets"
PROCESSED_DATA_DIR = "processed"
OUTPUT_CSV = "dataset_statistics.csv"
# ---------------------

def format_bytes(size_bytes):
    """Converte bytes para um formato legível (KB, MB, GB)."""
    if size_bytes > (1024**3):
        return f"{size_bytes / (1024**3):.2f} GB"
    if size_bytes > (1024**2):
        return f"{size_bytes / (1024**2):.2f} MB"
    if size_bytes > 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} Bytes"

def get_file_size(filepath):
    """Retorna o tamanho do arquivo em bytes."""
    try:
        return os.path.getsize(filepath)
    except Exception:
        return 0

def count_docs_in_original(filepath):
    """Conta o número total de documentos no arquivo original (JSON Array ou JSON Lines)."""
    print(f"    -> Contando documentos em {os.path.basename(filepath)} (pode levar um tempo)...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f_peek:
            chunk = f_peek.read(100).strip()
        
        count = 0
        if chunk.startswith('['):
            with open(filepath, 'rb') as f_in:
                parser = ijson.items(f_in, 'item')
                count = sum(1 for _ in parser)
        elif chunk.startswith('{'):
            with open(filepath, 'r', encoding='utf-8') as f_in:
                count = sum(1 for line in f_in if line.strip())
        
        print(f"    -> Contagem original: {count} documentos")
        return count
    except Exception as e:
        print(f"    -> Erro ao contar documentos em {filepath}: {e}")
        return 0

def get_doc_stats(filepath):
    """Calcula o número total de chaves e a profundidade máxima para um único arquivo JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        
        key_count = 0
        q_keys = deque([doc])
        while q_keys:
            node = q_keys.popleft()
            if isinstance(node, dict):
                key_count += len(node)
                q_keys.extend(node.values())
            elif isinstance(node, list):
                q_keys.extend(node)
                    
        depth = 0
        q_depth = deque([(doc, 1)])
        while q_depth:
            node, current_depth = q_depth.popleft()
            depth = max(depth, current_depth)
            if isinstance(node, dict):
                for value in node.values():
                    q_depth.append((value, current_depth + 1))
            elif isinstance(node, list):
                for item in node:
                    q_depth.append((item, current_depth + 1))
        
        return key_count, depth

    except Exception as e:
        print(f"   -> Erro ao analisar doc {filepath}: {e}")
        return 0, 0

def analyze_datasets():
    """Varre os diretórios, coleta estatísticas e salva no CSV."""
    print(f"Iniciando análise. Resultados serão salvos em '{OUTPUT_CSV}'")
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow([
            "Dataset",
            "Tamanho Original", "Docs Originais",
            "Docs na Amostra", "Tamanho da Amostra",
            "Min Chaves", "Max Chaves", "Média Chaves",
            "Min Profundidade", "Max Profundidade", "Média Profundidade"
        ])
        
        for file_name in os.listdir(ORIGINAL_DATA_DIR):
            if not (file_name.endswith(".json") or file_name.endswith(".jsonl")):
                continue
            
            dataset_name = os.path.splitext(file_name)[0]
            original_file_path = os.path.join(ORIGINAL_DATA_DIR, file_name)
            processed_docs_dir = os.path.join(PROCESSED_DATA_DIR, dataset_name, "documents")
            
            print(f"\n--- Analisando: {dataset_name} ---")
            
            original_size = format_bytes(get_file_size(original_file_path))
            original_doc_count = count_docs_in_original(original_file_path)
            
            sample_doc_count = 0
            sample_total_size_bytes = 0
            key_counts = []
            depths = []
            
            if not os.path.exists(processed_docs_dir):
                print(f"    -> Diretório de amostra não encontrado: {processed_docs_dir}")
                writer.writerow([dataset_name, original_size, original_doc_count, 0, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
                continue
            
            print(f"    -> Analisando documentos da amostra em: {processed_docs_dir}...")
            doc_files = [os.path.join(processed_docs_dir, f) for f in os.listdir(processed_docs_dir) if f.endswith('.json')]
            sample_doc_count = len(doc_files)
            
            for i, doc_path in enumerate(doc_files):
                if i % 100 == 0:
                    print(f"      -> Analisando doc {i+1}/{sample_doc_count}", end='\r')
                
                sample_total_size_bytes += get_file_size(doc_path)
                keys, depth = get_doc_stats(doc_path)
                if keys > 0:
                    key_counts.append(keys)
                    depths.append(depth)
            
            print(f"\n    -> Análise da amostra concluída.")
            
            if key_counts:
                min_keys, max_keys, avg_keys = min(key_counts), max(key_counts), sum(key_counts) / len(key_counts)
                min_depth, max_depth, avg_depth = min(depths), max(depths), sum(depths) / len(depths)
            else:
                min_keys = max_keys = avg_keys = min_depth = max_depth = avg_depth = 0

            writer.writerow([
                dataset_name,
                original_size, original_doc_count,
                sample_doc_count, format_bytes(sample_total_size_bytes),
                min_keys, max_keys, f"{avg_keys:.1f}",
                min_depth, max_depth, f"{avg_depth:.1f}"
            ])

    print(f"\n--- Análise Completa ---")
    print(f" Resultados salvos em '{OUTPUT_CSV}'.")

if __name__ == "__main__":
    analyze_datasets()
