import os
import json
import glob
from collections import defaultdict

# --- CONFIGURAÇÕES ---
SCHEMA_SOURCE_DIR = "processed/schema_documents/"
MASTER_SCHEMA_OUTPUT_DIR = "."
REQUIRED_THRESHOLD = 0.6 # Voltando para 0.6 como exemplo
TYPE_THRESHOLD = 0.75
# ---------------------

def load_and_repair_json(file_path):
    """
    Carrega um arquivo JSON, tentando repará-lo se for inválido,
    incluindo a remoção de BOM e extração de blocos JSON válidos.
    Retorna os dados do JSON ou None em caso de falha.
    """
    try:
        # Tenta carregar com o encoding 'utf-8-sig' que remove o BOM (Byte Order Mark)
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Se falhar, entramos no modo de reparo de formatação
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Encontra o primeiro '{' e o último '}' para extrair o JSON
            start_index = raw_content.find('{')
            end_index = raw_content.rfind('}')
            
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_slice = raw_content[start_index : end_index + 1]
                # Tenta carregar a fatia extraída
                return json.loads(json_slice)
            else:
                print(f"       -> Reparo de formatação falhou: Não foi possível encontrar um objeto JSON válido no arquivo.")
                return None
        except (json.JSONDecodeError, ValueError) as repair_e:
            print(f"       -> Reparo de formatação falhou: {repair_e}")
            return None
    except Exception as e:
        print(f"       -> Erro inesperado ao carregar/reparar JSON: {e}")
        return None

def repair_schema_structure(schema_node):
    """
    Verifica e corrige recursivamente erros estruturais comuns do LLM em um JSON Schema,
    como a falta da chave 'properties' em objetos e valores 'required' inválidos.
    """
    if not isinstance(schema_node, dict):
        return

    # Correção para a chave "required" sendo um booleano ou outro tipo inválido
    if "required" in schema_node:
        req_value = schema_node["required"]
        if not isinstance(req_value, list):
            # Se não for uma lista, tratamos como lista vazia
            schema_node["required"] = []
            if req_value is not None:
                print(f"       -> Corrigindo 'required' inválido (valor: {req_value}) para []")

    if "properties" in schema_node and isinstance(schema_node["properties"], dict):
        for key, prop in schema_node["properties"].items():
            repair_schema_structure(prop)
    else:
        # Lógica para detectar e corrigir objetos que deveriam ter "properties"
        potential_properties_content = {}
        has_schema_keywords = False # Flag para verificar se parece um schema object

        # Verifica se o nó atual se comporta como um schema de objeto malformado
        # Ou seja, tem "type": "object" mas as "propriedades" estão no mesmo nível
        if schema_node.get("type") == "object":
            has_schema_keywords = True

        keys_to_move = []
        for key, value in schema_node.items():
            # Um campo que deveria ser uma propriedade, mas está no mesmo nível do 'type: object'
            if isinstance(value, dict) and "type" in value:
                potential_properties_content[key] = value
                keys_to_move.append(key)
            elif key in ["title", "description", "default", "pattern", "format", "minimum", "maximum", "minLength", "maxLength"]:
                has_schema_keywords = True

        # Se parece um objeto malformado e tem conteúdo para mover para 'properties'
        if has_schema_keywords and potential_properties_content:
            # Garante que o tipo seja "object"
            schema_node["type"] = "object"
            
            # Move as chaves identificadas para dentro de "properties"
            for key_to_move in keys_to_move:
                del schema_node[key_to_move]
            
            # Se 'properties' já existe e é um dict, mesclamos. Senão, criamos.
            if "properties" not in schema_node or not isinstance(schema_node["properties"], dict):
                schema_node["properties"] = {}
            schema_node["properties"].update(potential_properties_content)
            
            print(f"       -> Corrigindo estrutura: Chaves movidas para 'properties' em '{schema_node.get('title', 'um objeto')}'")

            # Chamada recursiva para as novas propriedades
            for key, prop_node in schema_node["properties"].items():
                repair_schema_structure(prop_node)

def update_stats_tree(stats_node, schema_node):
    """
    Função recursiva para ler um schema e atualizar a árvore de estatísticas.
    """
    required_value = schema_node.get("required")
    required_fields = set(required_value) if isinstance(required_value, list) else set()
    
    for key, prop in schema_node.get("properties", {}).items():
        if not isinstance(prop, dict):
            continue

        if key not in stats_node:
            stats_node[key] = {
                "_stats": {
                    "appearances": 0,
                    "required_count": 0,
                    "type_counts": defaultdict(int),
                    "enum_values": set()  # Usamos um set para armazenar valores únicos de enum
                },
                "properties": {}
            }
        
        prop_stats = stats_node[key]["_stats"]
        prop_stats["appearances"] += 1
        
        if key in required_fields:
            prop_stats["required_count"] += 1
        
        raw_type = prop.get("type")
        types = []
        if isinstance(raw_type, str): types = [raw_type]
        elif isinstance(raw_type, list): types = [str(t) for t in raw_type if t is not None]
        elif raw_type is None: types = ["null"]
        
        for t in types:
            prop_stats["type_counts"][t] += 1
            
        if "enum" in prop and isinstance(prop["enum"], list):
            prop_stats["enum_values"].update(prop["enum"])

        if "object" in types and "properties" in prop:
            update_stats_tree(stats_node[key]["properties"], prop)


def build_schema_from_stats(stats_node):
    """
    Função recursiva para construir o schema final a partir da árvore de estatísticas.
    """
    final_schema = {"type": "object", "properties": {}}
    required_fields = []

    for key, node_data in stats_node.items():
        stats = node_data["_stats"]
        
        if stats["appearances"] == 0:
            continue

        # Lógica de 'required' permanece a mesma
        required_ratio = stats["required_count"] / stats["appearances"]
        if required_ratio >= REQUIRED_THRESHOLD:
            required_fields.append(key)

        # Se encontramos qualquer valor de enum para este campo, tratamos como enum
        if stats["enum_values"]:
            prop = {}
            # Define o tipo base (geralmente string, mas pode ser outro)
            non_null_types = [t for t in stats["type_counts"].keys() if t != "null"]
            base_type = non_null_types[0] if non_null_types else "string" # Pega o primeiro tipo não-nulo ou assume string
            
            # Adiciona 'null' ao tipo se foi observado
            has_null = "null" in stats["type_counts"]
            prop["type"] = [base_type, "null"] if has_null else base_type
            
            # Constrói a lista de enum final, lidando com None (para JSON null)
            all_enum_vals = stats["enum_values"]
            has_null_in_enum = None in all_enum_vals
            # Ordena apenas os valores não-nulos para evitar erro de comparação
            non_null_enum_vals = sorted([str(v) for v in all_enum_vals if v is not None])            
            final_enum_list = non_null_enum_vals
            if has_null_in_enum:
                final_enum_list.append(None) # Adiciona o nulo no final
            
            prop["enum"] = final_enum_list
            final_schema["properties"][key] = prop
            
            # Pula para a próxima propriedade, ignorando a lógica de TYPE_THRESHOLD
            continue 

        # A lógica original de TYPE_THRESHOLD só será executada se o campo não for um enum
        type_counts = stats["type_counts"]
        has_null = "null" in type_counts
        non_null_counts = {t: c for t, c in type_counts.items() if t != "null"}
        
        final_type = None
        if not non_null_counts:
            final_type = "null"
        else:
            total_non_null = sum(non_null_counts.values())
            if total_non_null == 0:
                 final_type = "string"
            else:
                winner_type = max(non_null_counts, key=non_null_counts.get)
                winner_ratio = non_null_counts[winner_type] / total_non_null
                
                if winner_ratio >= TYPE_THRESHOLD:
                    final_type = winner_type
                else:
                    final_type = sorted(list(non_null_counts.keys()))
                    if len(final_type) == 1: final_type = final_type[0]
        
        if has_null and final_type != "null":
            final_type = [final_type, "null"] if not isinstance(final_type, list) else sorted(final_type + ["null"])
        
        if final_type is None:
            final_type = "string"

        final_schema["properties"][key] = {"type": final_type}
        
        if "object" in str(final_type) and node_data["properties"]:
            nested_schema = build_schema_from_stats(node_data["properties"])
            final_schema["properties"][key].update(nested_schema)

    if required_fields:
        final_schema["required"] = sorted(required_fields)
        
    return final_schema

def process_directory(dir_path):
    """
    Orquestra as fases de coleta e geração para um único diretório.
    """
    dir_name = os.path.basename(dir_path)
    print(f"\n--- Processando o diretório: {dir_name} ---")
    
    schema_files = glob.glob(os.path.join(dir_path, '**/*.json'), recursive=True)
    if not schema_files:
        print(" Nenhum arquivo de schema encontrado neste diretório.")
        return

    print(f" Encontrados {len(schema_files)} arquivos. Iniciando a Fase 1: Coleta e Reparo...")

    stats_tree = {}
    valid_files_count = 0
    
    for i, file_path in enumerate(schema_files):
        print(f"   ({i+1}/{len(schema_files)}) Processando: {os.path.basename(file_path)}")
        
        # 1. Carrega e tenta reparar a formatação do JSON
        schema = load_and_repair_json(file_path)
        
        if schema is None:
            print(f"        Falha Crítica: Não foi possível ler/reparar JSON de {os.path.basename(file_path)}. Pulando.")
            continue
        
        # 2. Tenta reparar a estrutura interna do schema carregado
        repair_schema_structure(schema)

        # 3. Atualiza as estatísticas com o schema limpo e estruturalmente corrigido
        try:
            update_stats_tree(stats_tree, schema)
            valid_files_count += 1
        except Exception as e:
            print(f"        Erro na coleta de estatísticas após reparo de estrutura para {os.path.basename(file_path)}: {e}. Pulando.")
            continue


    if valid_files_count == 0:
        print(" Nenhuma estatística pôde ser coletada de arquivos válidos. Nenhum schema mestre será gerado.")
        return

    print(f"\n Análise concluída em {valid_files_count} arquivos válidos. Iniciando a Fase 2: Geração do Schema Mestre...")
    master_schema = build_schema_from_stats(stats_tree)
    
    output_filename = f"{dir_name}_master_schema.json"
    output_path = os.path.join(MASTER_SCHEMA_OUTPUT_DIR, output_filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(master_schema, f, indent=2, ensure_ascii=False)
        print(f" Fusão concluída! Schema mãe para '{dir_name}' salvo em: '{output_path}'")
    except Exception as e:
        print(f"\n Erro ao salvar o arquivo final para '{dir_name}': {e}")


def main():
    """
    Encontra todos os subdiretórios no diretório fonte e processa cada um deles.
    """
    print(f"Iniciando a fusão de schemas por diretório em: '{SCHEMA_SOURCE_DIR}'")
    try:
        subdirectories = [d.path for d in os.scandir(SCHEMA_SOURCE_DIR) if d.is_dir()]
    except FileNotFoundError:
        print(f" ERRO: O diretório fonte '{SCHEMA_SOURCE_DIR}' não foi encontrado."); return

    if not subdirectories:
        print(" Nenhum subdiretório encontrado para processar.")
        return
        
    for dir_path in subdirectories:
        process_directory(dir_path)
        
    print("\n--- Processo Finalizado ---")

if __name__ == "__main__":
    main()