
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import pandas as pd

# --- 1. CONFIGURAÇÃO ---

# Modelo pré-treinado a ser usado. TinyLlama é leve o suficiente para 8GB de RAM.
# Se estiver em uma máquina com mais de 16GB, pode tentar "microsoft/phi-2".
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Caminho para o manifesto do seu subconjunto de dados
SUBSET_MANIFEST_PATH = 'datasets/subset_1GB/manifest_subset.csv'

# Nova pasta onde os esquemas gerados pelo modelo de baseline serão salvos
OUTPUT_DIR = 'datasets/baseline_generated_schemas'

# Quantidade de arquivos do seu dataset que você quer processar
NUM_FILES_TO_PROCESS = 10 # <-- AJUSTE ESTE NÚMERO CONFORME NECESSÁRIO

def generate_baseline_schemas():
    """
    Carrega um modelo generalista e o utiliza para gerar esquemas para um
    número X de arquivos do dataset, salvando cada resultado.
    """
    print(f"--- Iniciando Geração de Esquemas Baseline com o modelo: {MODEL_ID} ---")
    
    # --- 2. SETUP ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Carregamento do modelo e tokenizer (feito apenas uma vez)
    print("Carregando modelo e tokenizer... Este processo é demorado e pode baixar vários GB.")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    device = torch.device("cpu") # Forçando CPU para garantir a execução em máquina sem GPU
    model.to(device)
    print(f"Modelo carregado no dispositivo: {device}")

    # Leitura do manifesto para obter a lista de arquivos
    try:
        manifest = pd.read_csv(SUBSET_MANIFEST_PATH)
        files_to_process = manifest.head(NUM_FILES_TO_PROCESS)
    except FileNotFoundError:
        print(f"ERRO: Manifesto não encontrado em '{SUBSET_MANIFEST_PATH}'.")
        return

    print(f"\nProcessando {len(files_to_process)} arquivos de um total de {len(manifest)}.")

    # --- 3. LOOP DE GERAÇÃO ---
    for index, row in files_to_process.iterrows():
        json_path = row['json_path']
        json_filename = os.path.basename(json_path)
        print(f"\n--- Processando arquivo [{index + 1}/{NUM_FILES_TO_PROCESS}]: {json_filename} ---")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
                json.loads(json_content) # Valida o JSON
        except Exception as e:
            print(f"  -> ERRO: Não foi possível ler ou validar o arquivo JSON. Pulando. ({e})")
            continue

        # Criação do prompt "Few-Shot"
        prompt = f"""
Gere um JSON Schema válido que descreve a estrutura do JSON Object fornecido.

---
Exemplo 1:
JSON Object:
{{
  "id": 1,
  "product_name": "Laptop"
}}

JSON Schema:
{{
  "type": "object",
  "properties": {{
    "id": {{
      "type": "integer"
    }},
    "product_name": {{
      "type": "string"
    }}
  }},
  "required": ["id", "product_name"]
}}
---
Exemplo 2 (Tarefa Real):
JSON Object:
{json_content}

JSON Schema:
"""
        
        inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False).to(device)

        # Geração da resposta
        print("  -> Gerando esquema... (Isso pode levar alguns minutos na CPU)")
        outputs = model.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.1)
        full_text = tokenizer.batch_decode(outputs)[0]
        generated_part = full_text[len(prompt):]
        
        # --- 4. SALVANDO O RESULTADO ---
        output_filename = json_filename.replace('.json', '.schema.json')
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        try:
            # Tenta formatar para salvar um JSON bonito
            parsed_schema = json.loads(generated_part)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_schema, f, indent=4)
            print(f"  -> SUCESSO: Esquema válido gerado e salvo em '{output_path}'")
        except (IndexError, json.JSONDecodeError):
            # Se falhar, salva o texto bruto para análise posterior
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"--- FALHA NA FORMATAÇÃO JSON ---\n{generated_part}")
            print(f"  -> AVISO: Saída não é um JSON válido. Resultado bruto salvo em '{output_path}'")

    print("\n--- Processo Concluído ---")

if __name__ == '__main__':
    generate_baseline_schemas()