import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import pandas as pd
import time

# --- 1. CONFIGURAÇÃO ---
# Modelo pré-treinado a ser usado. 'phi-2' é potente.
# Se a memória for um problema, volte para "TinyLlama/TinyLlama-1.1B-Chat-v1.0".
MODEL_ID = "microsoft/phi-2"

# Caminhos relativos à raiz do projeto
MASTER_SCHEMAS_FOLDER = 'master_schemas'
OUTPUT_JSON_DIR = 'datasets/synthetic_rawJson'

# O número total de documentos que você quer gerar PARA CADA esquema.
TOTAL_DOCS_PER_SCHEMA = 500 # <-- Altere este valor conforme necessário

def generate_synthetic_dataset():
    """
    Usa um modelo open source para gerar um grande número de documentos JSON
    a partir de um pequeno conjunto de esquemas-mãe.
    """
    print(f"--- Iniciando Geração de Dados Sintéticos com o modelo: {MODEL_ID} ---")
    os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
    
    print("Carregando modelo e tokenizer... (Pode demorar e baixar vários GB na 1ª vez)")
    # 'auto' detectará a GPU se disponível, senão usará CPU
    device_map = "auto"
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype="auto",
        trust_remote_code=True,
        device_map=device_map
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Modelo carregado e alocado nos dispositivos disponíveis.")

    try:
        schema_files = [f for f in os.listdir(MASTER_SCHEMAS_FOLDER) if f.endswith('.json')]
    except FileNotFoundError:
        print(f"ERRO: A pasta de esquemas-mãe '{MASTER_SCHEMAS_FOLDER}' não foi encontrada.")
        print("Certifique-se de criar esta pasta na raiz do projeto e colocar seus esquemas nela.")
        return

    # --- LOOP PRINCIPAL DE GERAÇÃO ---
    for schema_filename in schema_files:
        schema_path = os.path.join(MASTER_SCHEMAS_FOLDER, schema_filename)
        schema_base_name = os.path.splitext(schema_filename)[0]
        
        print(f"\n--- Processando Esquema-Mãe: {schema_filename} ---")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_content = f.read()

        # Verifica quantos arquivos já foram gerados para este esquema, para poder retomar
        # O 'try/except' lida com o caso da pasta ainda não existir
        try:
            generated_count = len([f for f in os.listdir(OUTPUT_JSON_DIR) if f.startswith(schema_base_name)])
        except FileNotFoundError:
            generated_count = 0
        
        print(f"Já existem {generated_count} documentos. A meta é {TOTAL_DOCS_PER_SCHEMA}.")

        while generated_count < TOTAL_DOCS_PER_SCHEMA:
            prompt = f"INSTRUCTION: You are a JSON data generator. Based on the provided JSON Schema, generate a single, valid JSON object that strictly conforms to the schema.\n\n### JSON Schema:\n{schema_content}\n\n### JSON Object:"
            
            inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False).to(model.device)

            print(f"  -> Gerando documento {generated_count + 1}/{TOTAL_DOCS_PER_SCHEMA}...")
            
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id
            )
            
            full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_part = full_text.split("### JSON Object:")[-1].strip()
            
            output_filename = f"{schema_base_name}_instance_{generated_count + 1}.json"
            output_path = os.path.join(OUTPUT_JSON_DIR, output_filename)

            try:
                parsed_json = json.loads(generated_part)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_json, f, indent=4)
                generated_count += 1
            except (IndexError, json.JSONDecodeError):
                print(f"  -> AVISO: O modelo gerou um JSON inválido. Tentando novamente.")
                time.sleep(1)
    
    print("\n--- Processo de Geração de Dados Sintéticos Concluído! ---")

if __name__ == '__main__':
    generate_synthetic_dataset()