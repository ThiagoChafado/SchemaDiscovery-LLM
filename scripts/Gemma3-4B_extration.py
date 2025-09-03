import json
import time
from openai import OpenAI
import ijson
import gc
from decimal import Decimal
import os

# --- CONFIGURAÇÕES ---
NOME_DO_MODELO = "gemma:2b" 

#Diretorio de entrada com os jsons
INPUT_DIR = 'datasets/twitter_documents/'
#Diretorio de saída dos jsons extraidos
OUTPUT_DIR = 'datasets/schema_documents/'

#Função para extrair os dados do Gemma3-4B
def extract_json_schema_from_files(input_dir, output_dir):

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            with open(input_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            # Start a new OpenAI client for each file to clear context
            client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

            prompt = (
                "Extract only the JSON schema (in JSON Schema format) for the following JSON document:\n"
                f"{json.dumps(data)}"
            )

            response = client.chat.completions.create(
                model=NOME_DO_MODELO,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,
                temperature=0
            )

            schema_text = response.choices[0].message.content.strip()
            try:
                schema_json = json.loads(schema_text)
            except Exception:
                schema_json = {"error": "Failed to parse schema", "raw": schema_text}

            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(schema_json, outfile, indent=2)

            del client
            gc.collect()
            time.sleep(1)

# Cria o diretório de saída se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)  
extract_json_schema_from_files(INPUT_DIR, OUTPUT_DIR)
