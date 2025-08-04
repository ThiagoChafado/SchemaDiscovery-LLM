# scripts/debug_kaggle_api.py
import subprocess
import io
import csv

def debug_kaggle_output():
    """
    Executa um único comando da API do Kaggle e imprime o cabeçalho
    do CSV para descobrirmos os nomes corretos das colunas.
    """
    print("--- Executando comando de teste na API do Kaggle... ---")
    
    # Usando um termo de busca simples para o teste
    search_term = "json"
    command = ["python3", "-m", "kaggle", "datasets", "list", "--search", search_term, "--csv"]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Decodifica a saída de bytes para string
        csv_output = result.stdout.decode('utf-8')
        
        print("\n--- SAÍDA BRUTA RECEBIDA DO KAGGLE ---")
        print(csv_output)
        
        # Processa a saída para encontrar o cabeçalho
        csv_file = io.StringIO(csv_output)
        reader = csv.reader(csv_file)
        header = next(reader)
        
        print("\n\n--- NOMES DAS COLUNAS (CABEÇALHO) ENCONTRADOS ---")
        print(header)
        print("\n-------------------------------------------------")

    except subprocess.CalledProcessError as e:
        print("\n--- ERRO AO EXECUTAR O COMANDO KAGGLE ---")
        print(e.stderr.decode('utf-8'))
    except Exception as e:
        print(f"\n--- OCORREU UM ERRO INESPERADO ---")
        print(e)

if __name__ == '__main__':
    debug_kaggle_output()
