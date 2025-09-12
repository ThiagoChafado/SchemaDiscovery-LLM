import json
import os
from llama_cpp import Llama

# --- CONFIGURAÇÕES ---

# 1. Cole aqui o caminho completo para o seu arquivo de modelo .gguf
MODEL_PATH = "/Users/thiagoalmeida/.lmstudio/models/lmstudio-community/gemma-3-4B-it-QAT-GGUF/gemma-3-4B-it-QAT-Q4_0.gguf"

# 2. Diretórios de entrada e saída
INPUT_DIR = 'datasets/twitter_documents/'
OUTPUT_DIR = 'datasets/schema_documents/'

# --- INICIALIZAÇÃO DO MODELO ---

print("Carregando o modelo... Isso pode levar um momento.")
# Esta é a parte mais importante. Configuramos o modelo para usar a aceleração do Mac.
try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=-1,  # 👈 A MÁGICA ACONTECE AQUI! -1 descarrega todas as camadas possíveis para a GPU (Metal).
        n_ctx=8196,       # Tamanho da janela de contexto.
        verbose=False      # Mostra os logs de inicialização do llama.cpp (útil para confirmar o uso de Metal).
    )
    print("Modelo carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")
    exit()

# --- FUNÇÃO DE EXTRAÇÃO DE SCHEMA ---

def extract_json_schema_from_files(input_dir, output_dir):
    """
    Itera sobre os arquivos JSON e gera o schema para cada um usando o modelo carregado.
    """
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        print(f"--- Processando arquivo: {filename} ---")

        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            # Gemma usa um formato de prompt específico. É bom segui-lo.
            prompt = (
                "Extract only the JSON schema (in JSON Schema format) for the following JSON document:\n\n"
                f"```json\n{json.dumps(data, indent=2)}\n```"
            )

            # Criamos a estrutura de mensagem para o modelo de chat
            messages = [
                {"role": "user", "content": prompt}
            ]

            print("Gerando schema...")
            
            # Chamada para o modelo
            response = llm.create_chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=8196,
            )

            # Extrai o conteúdo da resposta
            schema_text = response['choices'][0]['message']['content']
            
            print("Schema gerado com sucesso.")

            # Salva o resultado
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write(schema_text)
            
            print(f"Schema salvo em: {output_path}\n")

        except json.JSONDecodeError:
            print(f"Erro: O arquivo {filename} não é um JSON válido. Pulando.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao processar {filename}: {e}")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    extract_json_schema_from_files(INPUT_DIR, OUTPUT_DIR)   