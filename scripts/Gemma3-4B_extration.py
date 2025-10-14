import os
import csv
import json
import random
import signal
from datetime import datetime
from pathlib import Path  
from mlx_lm import load, generate

# --- CONFIGURAÇÕES ---
MANIFEST_PATH = "manifest.csv"
OUTPUT_DIR = "processed/schema_documents/"
LOG_FILE = "generation_log.csv"
MODEL_PATH_LOW = "/Users/thiagoalmeida/.lmstudio/models/mlx-community/gemma-3-4b-it-qat-4bit/"
MODEL_PATH_HIGH = "/Users/thiagoalmeida/.lmstudio/models/lmstudio-community/Qwen2.5-Coder-14B-Instruct-MLX-4bit/"
MAX_TOKENS = 8192
# Se um arquivo demorar mais que isso, provavelmente está em loop.
GENERATION_TIMEOUT_SECONDS = 120
# ---------------------------------------------------------------

# --- CLASSE E FUNÇÃO PARA CONTROLAR O TIMEOUT ---
class TimeoutError(Exception):
    """Exceção customizada para o timeout."""
    pass

def timeout_handler(signum, frame):
    """Esta função será chamada quando o alarme disparar."""
    raise TimeoutError(f"A geração excedeu o limite de {GENERATION_TIMEOUT_SECONDS} segundos.")
# -------------------------------------------------


def load_manifest(manifest_path):
    """Carrega o manifesto e embaralha a ordem dos arquivos."""
    entries = []
    # Usar um tratador de erros para o caso de o manifesto não ser encontrado
    try:
        with open(manifest_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Processa apenas se a coluna 'schema_generated' não for 'yes'/'true'/'1'
                if row.get("schema_generated", "").strip().lower() not in ("yes", "true", "1"):
                    entries.append(row)
        random.shuffle(entries)
        return entries
    except FileNotFoundError:
        print(f" ERRO: Arquivo de manifesto não encontrado em '{manifest_path}'")
        return []


def save_log_incremental(log_path, original_file_path, model_used, status, message=""):
    """Salva logs incrementalmente (append)."""
    log_exists = os.path.exists(log_path)
    with open(log_path, "a", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not log_exists:
            writer.writerow(["timestamp", "original_file", "model", "status", "message"])
        writer.writerow([
            datetime.now().isoformat(),
            original_file_path,  # Loga o caminho completo para evitar ambiguidade
            model_used,
            status,
            message.replace("\n", " ")[:2000]
        ])


def load_model(model_path, model_name):
    """Carrega modelo MLX."""
    print(f"\n  Carregando modelo MLX: {model_name} ...")
    try:
        model, tokenizer = load(model_path)
        print(f" Modelo {model_name} carregado com sucesso!\n")
        return model, tokenizer
    except Exception as e:
        print(f" Erro ao carregar modelo {model_name}: {e}")
        return None, None


def extract_schema_from_file(model, tokenizer, input_path, output_path):
    """Extrai o schema JSON usando o modelo MLX (versão otimizada e robusta)."""
    with open(input_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    prompt = (
        "You are a data schema extraction expert.\n"
        "Generate only the JSON Schema (in standard JSON Schema Draft 2020-12 format) for the following JSON document.\n\n"
        "- Include 'required' when it can be clearly inferred.\n"
        "- If a field can be null, use 'type': ['string', 'null'] (or the appropriate type).\n"
        "- Do not include 'description' for any field.\n"
        "- Output only the schema, no explanations or extra text. End your response after the final '}'.\n\n"
        "Input JSON:\n"
        f"```json\n{json.dumps(data, indent=2)}\n```\n\n"
        "JSON Schema:\n"
        "```json\n"
    )
    
    response = generate(
        model=model,
        tokenizer=tokenizer,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        verbose=True
    )

    schema_text = ""
    try:
        # Lógica de extração do bloco JSON da resposta
        start_index = response.find('{')
        end_index = response.rfind('}') + 1
        if start_index != -1 and end_index > start_index:
            schema_text = response[start_index:end_index]
            json.loads(schema_text)  # Tenta validar o JSON extraído
        else:
            schema_text = response.strip()
            print("Aviso: Bloco JSON completo não foi encontrado. Usando resposta bruta.")
    except json.JSONDecodeError:
        # Se a extração falhar, usa a resposta bruta
        schema_text = response.strip()
        print(f"Aviso: JSON extraído é inválido. Salvando a resposta bruta.")

    # Garante que o diretório de saída exista
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as outfile:
        # Tenta formatar o JSON antes de salvar para melhor legibilidade
        try:
            parsed_json = json.loads(schema_text)
            json.dump(parsed_json, outfile, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Se o texto final não for um JSON válido, salva como texto bruto
            outfile.write(schema_text)


def main():
    """Função principal com a lógica de caminho de arquivo corrigida."""
    manifest_entries = load_manifest(MANIFEST_PATH)
    if not manifest_entries:
        print("Nenhum arquivo pendente no manifesto para processar.")
        return

    print(f"Total de arquivos pendentes: {len(manifest_entries)}")

    model_low, tokenizer_low = None, None
    model_high, tokenizer_high = None, None
    
    signal.signal(signal.SIGALRM, timeout_handler)
    
    for i, entry in enumerate(manifest_entries, 1):
        original_file_path = entry["file"]
        
        try:
            full_path = Path(original_file_path)
            # O nome do dataset será a segunda parte do caminho (índice 1)
            dataset_name = full_path.parts[1]
            base_name = full_path.name
            object_type = entry.get("object_type", "unknown")
            
            # Constrói o novo caminho de saída que inclui o nome do dataset
            output_path = os.path.join(OUTPUT_DIR, dataset_name, object_type, base_name)
        except IndexError:
            print(f" ERRO: O caminho do arquivo '{original_file_path}' não segue a estrutura esperada 'processed/dataset/...'. Pulando.")
            save_log_incremental(LOG_FILE, original_file_path, "N/A", "failed", "Invalid file path structure in manifest")
            continue
        
        complexity = entry.get("complexity", "high").lower()
        model_name = "N/A"

        print(f"\n--- Processando arquivo {i}/{len(manifest_entries)}: {original_file_path} ---")
        
        signal.alarm(GENERATION_TIMEOUT_SECONDS)
        
        try:
            if complexity == "low":
                if model_low is None:
                    model_low, tokenizer_low = load_model(MODEL_PATH_LOW, "Gemma 3-4B (MLX)")
                current_model, current_tokenizer = model_low, tokenizer_low
                model_name = "Gemma 3-4B (MLX)"
            else:
                continue
                if model_high is None:
                    model_high, tokenizer_high = load_model(MODEL_PATH_HIGH, "Qwen 2.5-Coder 14B (MLX)")
                current_model, current_tokenizer = model_high, tokenizer_high
                model_name = "Qwen 2.5-Coder 14B (MLX)"

            if current_model is None or current_tokenizer is None:
                raise RuntimeError(f"Falha ao carregar o modelo {model_name}.")

            extract_schema_from_file(current_model, current_tokenizer, original_file_path, output_path)
            
            save_log_incremental(LOG_FILE, original_file_path, model_name, "success", f"Schema saved to {output_path}")
            print(f"Schema salvo com sucesso em: {output_path}")

        except TimeoutError as e:
            save_log_incremental(LOG_FILE, original_file_path, model_name, "failed", f"Timeout: {e}")
            print(f" Timeout ao processar {original_file_path}. Pulando para o próximo.")
        
        except Exception as e:
            save_log_incremental(LOG_FILE, original_file_path, model_name, "failed", str(e))
            print(f" Erro ao processar {original_file_path}: {e}")
        
        finally:
            signal.alarm(0)

if __name__ == "__main__":
    if not hasattr(signal, 'SIGALRM'):
        print("Aviso: O mecanismo de timeout com 'signal' não é suportado neste sistema operacional (ex: Windows).")
        print("O script será executado sem proteção contra loops infinitos.")
    main()