import os
import json

# --- Configurações ---
# Nome do arquivo JSON original (grande)
entry_file = 'datasets/twitter.json'
# Nome do novo arquivo que será criado (reduzido)
output_file = 'datasets/twitter_reduzido.json'
# Tamanho final desejado em Megabytes (MB)
size_target = 500
# --------------------

def reduce_json_file(entry_file, output_file, size_target):
    """
    Lê um arquivo JSON Lines e cria uma versão menor, fazendo uma amostragem
    das linhas para atingir um tamanho de arquivo alvo aproximado.
    """
    try:
        # 1. Obter o tamanho do arquivo original em bytes
        original_size = os.path.getsize(entry_file)
        if original_size == 0:
            print("Erro: O arquivo de entrada está vazio.")
            return
            
        size_target_bytes = size_target * 1024 * 1024
        
        # 2. Calcular a proporção de redução
        # Se o arquivo original já for menor que o alvo, copia tudo.
        if original_size <= size_target_bytes:
            print("O arquivo original já é menor ou igual ao tamanho alvo. Copiando o arquivo...")
            import shutil
            shutil.copy(entry_file, output_file)
            print(f"Arquivo copiado para '{output_file}'.")
            return

        sampling_rate = round(original_size / size_target_bytes)
        print(f"Tamanho original: {original_size / (1024*1024):.2f} MB")
        print(f"Tamanho alvo: ~{size_target} MB")
        print(f"Amostragem: Mantendo 1 a cada {sampling_rate} linhas.")

        # 3. Ler o arquivo grande e escrever no pequeno
        line_counter = 0
        write_lines = 0
        with open(entry_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                # Usamos o operador de módulo (%) para selecionar as linhas
                if line_counter % sampling_rate == 0:
                    # Apenas escreve a line selecionada no novo arquivo
                    f_out.write(line)
                    write_lines += 1
                line_counter += 1

        print("\n--- Concluído! ---")
        print(f"Total de lines lidas: {line_counter}")
        print(f"Total de lines escritas: {write_lines}")

        final_size_bytes = os.path.getsize(output_file)
        print(f"Tamanho do novo arquivo: {final_size_bytes / (1024*1024):.2f} MB")
        print(f"Arquivo reduzido salvo como: '{output_file}'")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{entry_file}' não foi encontrado. Verifique o nome e o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

#Função para transformar json inline para json normal
def jsonlines_tojson(jsonline_file, json_file):
    """
    Converte um arquivo JSON Lines (.jsonl) para um arquivo JSON normal (.json) para utilizar melhor no modelo.
    """
    try:
        data = []
        with open(jsonline_file, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                data.append(json.loads(line))
        
        with open(json_file, 'w', encoding='utf-8') as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)
        
        print(f"Arquivo convertido salvo como: '{json_file}'")
    except Exception as e:
        print(f"Ocorreu um erro ao converter o arquivo: {e}")



#Funçao para ler o arquivo json e separar em arquivos menores, um arquivo por documento json

def split_json_file(input_file, output_dir):
    """
    Lê um arquivo JSON contendo uma lista de objetos e cria arquivos JSON separados,
    um para cada objeto na lista.
    """
    try:
        # Cria o diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        with open(input_file, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)
        
        if not isinstance(data, list):
            print("Erro: O arquivo JSON de entrada não contém uma lista de objetos.")
            return
        
        for idx, item in enumerate(data):
            output_file = os.path.join(output_dir, f'document_{idx + 1}.json')
            with open(output_file, 'w', encoding='utf-8') as f_out:
                json.dump(item, f_out, ensure_ascii=False, indent=4)
        
        print(f"Arquivos separados salvos em: '{output_dir}'")
    
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado. Verifique o nome e o caminho.")
    except json.JSONDecodeError:
        print("Erro: O arquivo JSON de entrada está malformado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Executa a função
reduce_json_file(entry_file, output_file, size_target)
jsonlines_tojson(output_file, 'datasets/twitter_reduzido.json')
split_json_file('datasets/twitter_reduzido.json', 'datasets/twitter_documents')