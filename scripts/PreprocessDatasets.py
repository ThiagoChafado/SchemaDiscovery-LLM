import os
import json
import shutil
import ijson

# --- Configurações ---
input_dir = "datasets"  # onde estão os arquivos originais
output_base_dir = "processed"
size_target = 80  # MB para cada arquivo reduzido
# --------------------

def cleanup_intermediate_files(directory):
    """
    Limpa os arquivos intermediários (como os reduzidos e convertidos) de um diretório,
    mantendo apenas as subpastas (ex: 'documents').
    """
    print(f"  Limpando arquivos intermediários em: {directory}")
    try:
        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)
            # Verifica se é um arquivo (e não uma pasta)
            if os.path.isfile(item_path):
                os.remove(item_path)
                print(f"   - Removido: {item_name}")
        print("  ✔ Limpeza concluída.")
        return True
    except Exception as e:
        print(f"  ERRO durante a limpeza: {e}")
        return False


def reduce_and_sample_file(entry_file, output_file, size_target):
    """
    Lê um arquivo JSON ou JSON Lines e cria uma versão menor, fazendo amostragem
    dos elementos para atingir um tamanho de arquivo alvo aproximado.
    Esta versão detecta o formato do arquivo pelo conteúdo, não pela extensão.
    """
    try:
        original_size = os.path.getsize(entry_file)
        if original_size == 0:
            print(f"  Arquivo vazio: {entry_file}")
            return False

        size_target_bytes = size_target * 1024 * 1024

        if original_size <= size_target_bytes:
            print("  Arquivo já é menor que o alvo, copiando...")
            shutil.copy(entry_file, output_file)
            return True

        sampling_rate = round(original_size / size_target_bytes)
        if sampling_rate < 1:
            sampling_rate = 1

        print(
            f"  {entry_file} - {original_size / (1024*1024):.2f} MB → alvo {size_target} MB | Amostragem: 1 a cada {sampling_rate}"
        )

        file_format = None
        with open(entry_file, 'r', encoding='utf-8') as f_peek:
            chunk = f_peek.read(100).strip()
            if chunk.startswith('['):
                file_format = 'json_array'
                print("  Formato detectado: JSON Array")
            elif chunk.startswith('{'):
                file_format = 'json_lines'
                print("  Formato detectado: JSON Lines")
            else:
                print(f"  ERRO: Formato de arquivo desconhecido em {entry_file}. Não começa com '[' ou '{{'.")
                return False

        counter = 0
        items_written = 0

        with open(output_file, "w", encoding="utf-8") as f_out:
            if file_format == 'json_lines':
                with open(entry_file, "r", encoding="utf-8") as f_in:
                    for line in f_in:
                        if counter % sampling_rate == 0:
                            f_out.write(line)
                            items_written += 1
                        counter += 1
            elif file_format == 'json_array':
                with open(entry_file, "rb") as f_in:
                    f_out.write('[')
                    first_item = True
                    parser = ijson.items(f_in, 'item')
                    for item in parser:
                        if counter % sampling_rate == 0:
                            if not first_item:
                                f_out.write(',\n')
                            json.dump(item, f_out, ensure_ascii=False, indent=2)
                            first_item = False
                            items_written += 1
                        counter += 1
                    f_out.write('\n]')

        final_size_bytes = os.path.getsize(output_file)
        print(
            f"  Redução concluída: {final_size_bytes / (1024*1024):.2f} MB ({items_written} itens)"
        )
        return True
    except Exception as e:
        print(f"  Erro ao reduzir {entry_file}: {e}")
        return False


def jsonlines_tojson(jsonline_file, json_file):
    """Converte JSONL → JSON (array de objetos)."""
    try:
        data = []
        with open(jsonline_file, "r", encoding="utf-8") as f_in:
            for line in f_in:
                if line.strip():
                    data.append(json.loads(line))
        with open(json_file, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)
        print(f" ✔ Convertido JSONL → JSON: {json_file}")
        return True
    except Exception as e:
        print(f"  Erro ao converter {jsonline_file}: {e}")
        return False


def split_json_file(input_file, output_dir):
    """Divide JSON (lista de objetos) em arquivos individuais."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(input_file, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
        if not isinstance(data, list):
            print("  O arquivo não contém uma lista JSON:", input_file)
            return False
        for idx, item in enumerate(data):
            output_file = os.path.join(output_dir, f"document_{idx+1}.json")
            with open(output_file, "w", encoding="utf-8") as f_out:
                json.dump(item, f_out, ensure_ascii=False, indent=4)
        print(f"  {len(data)} documentos salvos em: {output_dir}")
        return True
    except Exception as e:
        print(f"  Erro ao dividir {input_file}: {e}")
        return False


def process_all_files(input_dir, output_base_dir, size_target):
    os.makedirs(output_base_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if not (file_name.endswith(".json") or file_name.endswith(".jsonl")):
            continue

        file_path = os.path.join(input_dir, file_name)
        name, ext = os.path.splitext(file_name)
        output_dir = os.path.join(output_base_dir, name)
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n--- Processando: {file_name} ---")

        reduced_file = os.path.join(output_dir, f"{name}_reduced{ext}")

        if reduce_and_sample_file(file_path, reduced_file, size_target):
            final_json_to_split = None
            
            # Após reduzir, precisamos ter um arquivo JSON Array para dividir.
            with open(reduced_file, 'r', encoding='utf-8') as f_peek:
                chunk = f_peek.read(100).strip()
                if not chunk:
                    print(f"  Arquivo reduzido está vazio. Pulando divisão e limpeza.")
                    continue
                
                if chunk.startswith('['):
                    final_json_to_split = reduced_file
                elif chunk.startswith('{'):
                    converted_json = os.path.join(output_dir, f"{name}_reduced_converted.json")
                    if jsonlines_tojson(reduced_file, converted_json):
                        final_json_to_split = converted_json

            if final_json_to_split:
                docs_dir = os.path.join(output_dir, "documents")
                # Se a divisão for bem-sucedida, limpe os arquivos
                if split_json_file(final_json_to_split, docs_dir):
                    cleanup_intermediate_files(output_dir) # <<< CHAMADA DA FUNÇÃO DE LIMPEZA
            else:
                 print(f"  Não foi possível determinar o arquivo final para dividir para {file_name}")


if __name__ == "__main__":
    process_all_files(input_dir, output_base_dir, size_target)