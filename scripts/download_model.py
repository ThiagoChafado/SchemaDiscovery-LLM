# scripts/download_model.py
from huggingface_hub import snapshot_download
import os

# --- ALTERAÇÃO AQUI ---
MODEL_ID = "gpt2"
LOCAL_MODEL_PATH = "gpt2-local-cache" # Novo nome para a pasta

def download_model_to_local_dir():
    if os.path.exists(LOCAL_MODEL_PATH):
        print(f"Modelo já existe em '{LOCAL_MODEL_PATH}'. Pulando o download.")
        return

    print(f"Baixando o modelo '{MODEL_ID}' para a pasta local '{LOCAL_MODEL_PATH}'...")
    try:
        # Usando o argumento antigo 'cache_dir' para compatibilidade
        snapshot_download(
            repo_id=MODEL_ID,
            cache_dir=LOCAL_MODEL_PATH
        )
        print(f"\n[SUCESSO] Download do modelo concluído para: '{LOCAL_MODEL_PATH}'")
    except Exception as e:
        print(f"\n[ERRO] Falha no download do modelo: {e}")

if __name__ == '__main__':
    try:
        import huggingface_hub
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
    
    download_model_to_local_dir()

