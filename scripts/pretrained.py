
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os

# --- 1. CONFIGURAÇÃO ---

# ALTERAÇÃO: Usando o modelo TinyLlama, que é muito menor e mais leve.
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Aponte para um dos seus arquivos JSON para testar.
JSON_FILE_TO_TEST = 'datasets/subset_1GB/rawJson/retail-sales-retail-excluding-food-services_metadata.json' # <-- MUDE AQUI PARA TESTAR OUTROS ARQUIVOS

def test_generalist_model():
    print(f"--- Testando o Modelo Generalista Pré-treinado: {MODEL_ID} ---")

    # --- 2. CARREGAMENTO DO MODELO E TOKENIZER ---
    print("Carregando modelo e tokenizer...")
    print("AVISO: Na primeira vez, isso irá baixar ~4.5 GB de dados. Tenha paciência.")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

    # Força o uso da CPU
    device = torch.device("cpu")
    model.to(device)
    print(f"Modelo carregado no dispositivo: {device}")

    # --- 3. LEITURA DO ARQUIVO JSON E CRIAÇÃO DO PROMPT ---
    try:
        with open(JSON_FILE_TO_TEST, 'r', encoding='utf-8') as f:
            json_content = f.read()
            json.loads(json_content) 
    except Exception as e:
        print(f"Erro ao ler ou validar o arquivo JSON: {JSON_FILE_TO_TEST}")
        print(e)
        return

    # O "Few-Shot Prompting" continua sendo a melhor estratégia
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

    print("\n--- Gerando esquema para o arquivo:", JSON_FILE_TO_TEST, "---")
    print("AVISO: A geração na CPU será LENTA, pode levar vários minutos.")

    # --- 4. GERAÇÃO DA RESPOSTA ---
    inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False).to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.1,
        top_p=0.95,
        top_k=50
    )
    
    full_text = tokenizer.batch_decode(outputs)[0]
    generated_part = full_text[len(prompt):] 

    # --- 5. EXIBIÇÃO DO RESULTADO ---
    print("\n--- Esquema Gerado pelo Modelo ---")
    try:
        parsed_schema = json.loads(generated_part)
        print(json.dumps(parsed_schema, indent=4))
    except (IndexError, json.JSONDecodeError):
        print("(Não foi possível formatar a saída como JSON. Exibindo texto bruto:)")
        print(generated_part)

if __name__ == '__main__':
    test_generalist_model()