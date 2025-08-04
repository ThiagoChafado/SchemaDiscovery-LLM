# scripts/generate_baseline_schemas.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import pandas as pd

# --- 1. CONFIGURAÇÃO ---
# MUDANÇA: Usando um modelo mais potente, que é melhor em seguir instruções.
MODEL_ID = "microsoft/phi-2"

# Aponte para o manifesto do seu subconjunto de dados.
SUBSET_MANIFEST_PATH = 'datasets/subset_1GB/manifest_subset.csv'
# Nova pasta onde os esquemas gerados serão salvos.
OUTPUT_DIR = 'datasets/baseline_generated_schemas_phi2'
# Quantidade de arquivos aleatórios para processar.
NUM_FILES_TO_PROCESS = 10

def generate_baseline_schemas():
    print(f"--- Iniciando Geração de Esquemas com o modelo: {MODEL_ID} ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Carregando modelo e tokenizer... (Download pode ser grande na 1ª vez)")
    # trust_remote_code=True é necessário para o phi-2
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype="auto",
        trust_remote_code=True
    )

    # Adiciona um pad token se não existir, para evitar avisos.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Modelo carregado no dispositivo: {device}")

    manifest = pd.read_csv(SUBSET_MANIFEST_PATH)
    num_to_sample = min(NUM_FILES_TO_PROCESS, len(manifest))
    files_to_process = manifest.sample(n=num_to_sample, random_state=42)
    print(f"\nSelecionados {len(files_to_process)} arquivos aleatórios para processar.")

    for index, row in files_to_process.iterrows():
        json_path = row['json_path']
        json_filename = os.path.basename(json_path)
        print(f"\n--- Processando arquivo [{index + 1}/{num_to_sample}]: {json_filename} ---")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = f.read()

        # --- PROMPT MELHORADO COM SINAL DE PARADA (eos_token) ---
        prompt = f"""INSTRUÇÃO: Gere um JSON Schema válido que descreve a estrutura do JSON Object a seguir.

### JSON Object:
{{
  "id": 1,
  "product_name": "Laptop"
}}

### JSON Schema:
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
}}{tokenizer.eos_token} 
---
### JSON Object:
{json_content}

### JSON Schema:
"""
        
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        print("  -> Gerando esquema...")
        
        # --- GERAÇÃO OTIMIZADA E CONTROLADA ---
        outputs = model.generate(
            **inputs, 
            max_new_tokens=512,
            # Força a parada quando o token de fim de sequência é gerado
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
            do_sample=True,
            temperature=0.1,
            top_p=0.95
        )
        
        full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extrai apenas a parte gerada após o último marcador
        generated_part = full_text.split("### JSON Schema:")[-1].strip()
        
        output_filename = json_filename.replace('.json', '.schema.json')
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        try:
            parsed_schema = json.loads(generated_part)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_schema, f, indent=4)
            print(f"  -> SUCESSO: Esquema válido gerado e salvo em '{output_path}'")
        except (IndexError, json.JSONDecodeError):
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"--- FALHA NA FORMATAÇÃO JSON ---\n{generated_part}")
            print(f"  -> AVISO: Saída não é um JSON válido. Resultado bruto salvo em '{output_path}'")

    print("\n--- Processo Concluído ---")

if __name__ == '__main__':
    generate_baseline_schemas()
