import json
import time
from openai import OpenAI
import ijson
import gc
from decimal import Decimal

# --- CONFIGURAÇÕES ---
CLIENTE_OPENAI = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
NOME_DO_MODELO = "gemma:2b" 
ARQUIVO_ENTRADA = 'datasets/twitter_reduzido.json'
ARQUIVO_SAIDA = 'datasets/esquemas_extraidos.txt'

# --------------------

# Função para extrair o esquema de um JSON
def extrair_esquema_json():
    with open(ARQUIVO_ENTRADA, 'r') as f_in, open(ARQUIVO_SAIDA, 'w') as f_out:
        objetos = ijson.items(f_in, 'item')
        for obj in objetos:
            prompt = f"Extract the schema from the following JSON object:\n{json.dumps(obj, ensure_ascii=False, default=str)}"
            resposta = CLIENTE_OPENAI.chat.completions.create(
                model=NOME_DO_MODELO,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0
            )
            schema = resposta.choices[0].message.content.strip()
            f_out.write(schema + '\n')
            gc.collect()
            time.sleep(0.5)
            
            
# Executa a função
extrair_esquema_json()
