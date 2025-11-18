import os
import json
import glob
from collections import defaultdict

# --- CONFIGURAÇÕES ---
SCHEMA_SOURCE_DIR = "processed/schema_documents/"
MASTER_SCHEMA_OUTPUT_DIR = "."
REQUIRED_THRESHOLD = 1
TYPE_THRESHOLD = 0.75
# ---------------------

def load_and_repair_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            start_index = raw_content.find('{')
            end_index = raw_content.rfind('}')
            if start_index != -1 and end_index > start_index:
                json_slice = raw_content[start_index:end_index + 1]
                return json.loads(json_slice)
            else:
                return None
        except (json.JSONDecodeError, ValueError):
            return None
    except Exception:
        return None


def repair_schema_structure(schema_node):
    """
    Corrige erros estruturais em JSON Schemas gerados por LLMs.
    Inclui:
    - Conversão de 'required': true para inclusão na lista 'required' do pai.
    - Garantia de estrutura válida de objetos e propriedades.
    """
    if not isinstance(schema_node, dict):
        return

    if "required" in schema_node and not isinstance(schema_node["required"], list):
        schema_node["required"] = []

    if "properties" in schema_node and isinstance(schema_node["properties"], dict):
        if "required" not in schema_node or not isinstance(schema_node["required"], list):
            schema_node["required"] = []

        for key, prop in list(schema_node["properties"].items()):
            if isinstance(prop, dict):
                # Move 'required': true do campo para a lista de required do pai
                if prop.get("required") is True:
                    if key not in schema_node["required"]:
                        schema_node["required"].append(key)
                    del prop["required"]

                repair_schema_structure(prop)

    else:
        potential_properties_content = {}
        has_schema_keywords = False

        if schema_node.get("type") == "object":
            has_schema_keywords = True

        keys_to_move = []
        for key, value in schema_node.items():
            if isinstance(value, dict) and "type" in value:
                potential_properties_content[key] = value
                keys_to_move.append(key)
            elif key in [
                "title", "description", "default", "pattern", "format",
                "minimum", "maximum", "minLength", "maxLength"
            ]:
                has_schema_keywords = True

        if has_schema_keywords and potential_properties_content:
            schema_node["type"] = "object"
            for key_to_move in keys_to_move:
                del schema_node[key_to_move]
            if "properties" not in schema_node or not isinstance(schema_node["properties"], dict):
                schema_node["properties"] = {}
            schema_node["properties"].update(potential_properties_content)

            for key, prop_node in schema_node["properties"].items():
                repair_schema_structure(prop_node)


def update_stats_tree(stats_node, schema_node):
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
                    "enum_values": set()
                },
                "properties": {}
            }

        prop_stats = stats_node[key]["_stats"]
        prop_stats["appearances"] += 1

        if key in required_fields:
            prop_stats["required_count"] += 1

        raw_type = prop.get("type")
        types_to_add = []

        if isinstance(raw_type, str):
            types_to_add = [raw_type]
        elif isinstance(raw_type, list):
            for t in raw_type:
                if t is None:
                    types_to_add.append("null")
                else:
                    types_to_add.append(str(t))
        elif raw_type is None:
            types_to_add = ["null"]

        for t in types_to_add:
            prop_stats["type_counts"][t] += 1

        if "enum" in prop and isinstance(prop["enum"], list):
            prop_stats["enum_values"].update(prop["enum"])

        if "object" in types_to_add and "properties" in prop:
            update_stats_tree(stats_node[key]["properties"], prop)


def build_schema_from_stats(stats_node, total_documents):
    final_schema = {"type": "object", "properties": {}}
    required_fields = []

    if total_documents == 0:
        return final_schema

    for key, node_data in stats_node.items():
        stats = node_data["_stats"]
        prop = {}

        if stats["appearances"] == 0:
            continue

        ratio = stats["required_count"] / total_documents
        if ratio >= REQUIRED_THRESHOLD:
            required_fields.append(key)

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
                    if len(final_type) == 1:
                        final_type = final_type[0]

        if has_null and final_type != "null":
            final_type = [final_type, "null"] if not isinstance(final_type, list) else sorted(final_type + ["null"])

        if final_type is None:
            final_type = "string"

        prop["type"] = final_type

        if "object" in str(final_type) and node_data["properties"]:
            nested_schema = build_schema_from_stats(node_data["properties"], total_documents)
            current_type = prop["type"]
            prop.update(nested_schema)
            prop["type"] = current_type

        final_schema["properties"][key] = prop

    if required_fields:
        final_schema["required"] = sorted(required_fields)

    return final_schema


def process_directory(dir_path):
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
        schema = load_and_repair_json(file_path)
        if schema is None:
            continue

        repair_schema_structure(schema)

        try:
            update_stats_tree(stats_tree, schema)
            valid_files_count += 1
        except Exception as e:
            print(f"        Erro na coleta de estatísticas para {os.path.basename(file_path)}: {e}. Pulando.")
            continue

    if valid_files_count == 0:
        print(" Nenhuma estatística pôde ser coletada de arquivos válidos. Nenhum schema mestre será gerado.")
        return

    print(f"\n Análise concluída em {valid_files_count} arquivos válidos. Iniciando a Fase 2: Geração do Schema Mestre...")
    master_schema = build_schema_from_stats(stats_tree, valid_files_count)
    output_filename = f"{dir_name}_master_schema.json"
    output_path = os.path.join(MASTER_SCHEMA_OUTPUT_DIR, output_filename)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(master_schema, f, indent=2, ensure_ascii=False)
        print(f" Fusão concluída! Schema mãe para '{dir_name}' salvo em: '{output_path}'")
    except Exception as e:
        print(f"\n Erro ao salvar o arquivo final para '{dir_name}': {e}")


def main():
    print(f"Iniciando a fusão de schemas por diretório em: '{SCHEMA_SOURCE_DIR}'")
    try:
        subdirectories = [d.path for d in os.scandir(SCHEMA_SOURCE_DIR) if d.is_dir()]
    except FileNotFoundError:
        print(f" ERRO: O diretório fonte '{SCHEMA_SOURCE_DIR}' não foi encontrado.")
        return

    if not subdirectories:
        print(" Nenhum subdiretório encontrado para processar.")
        return

    for dir_path in subdirectories:
        process_directory(dir_path)

    print("\n--- Processo Finalizado ---")


if __name__ == "__main__":
    main()
