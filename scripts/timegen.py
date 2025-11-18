import os
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
import statistics

# --- CONFIGURAÇÕES ---
LOG_FILE = "generation_log.csv"
OUTPUT_FILE = "generation_time_summary.csv"

# Limites para a análise
MAX_SAMPLES_PER_DATASET = 500  # Analisa apenas os primeiros 1000 documentos
MAX_GAP_SECONDS = 1800         # Ignora paradas maiores que 30 minutos
# ---------------------

def get_dataset_name_from_path(file_path_str):
    """
    Extrai o nome do dataset do caminho do arquivo.
    """
    try:
        return Path(file_path_str).parts[1]
    except IndexError:
        return None

def analyze_log_times_summary():
    """
    Lê o log, coleta até 1000 tempos de geração válidos por dataset,
    identifica o modelo predominante e salva um RESUMO em CSV.
    """
    # Armazena tuplas: (timestamp, file_path, model_name)
    dataset_logs = defaultdict(list)
    
    print(f"🔎 Lendo o arquivo de log: {LOG_FILE}...")
    
    try:
        with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                try:
                    # O formato esperado é: timestamp, file, model, status, message
                    timestamp_str = row[0]
                    file_path = row[1]
                    model_name = row[2] # A coluna do modelo é a 3ª (índice 2)
                    status = row[3]
                    
                    if status.strip().lower() != 'success':
                        continue
                        
                    timestamp = datetime.fromisoformat(timestamp_str)
                    dataset_name = get_dataset_name_from_path(file_path)
                    
                    if dataset_name:
                        dataset_logs[dataset_name].append((timestamp, file_path, model_name))
                        
                except (IndexError, ValueError):
                    continue
                    
    except FileNotFoundError:
        print(f"❌ ERRO: O arquivo de log '{LOG_FILE}' não foi encontrado.")
        return

    print(f"✅ Leitura concluída. Processando dados...")

    # Lista para armazenar os resultados finais
    summary_results = []
    
    for dataset_name, logs in dataset_logs.items():
        print(f"\n--- Processando: {dataset_name} ---")
        
        if len(logs) < 2:
            print("   -> Não há logs suficientes para calcular tempos.")
            continue
            
        # Ordena os logs por timestamp
        logs.sort(key=lambda x: x[0])
        
        valid_time_gaps = []
        models_used = [] # Lista para guardar os modelos das amostras válidas
        
        # Itera sobre os logs até atingir o limite de amostras
        for i in range(1, len(logs)):
            # PARADA: Se já coletamos 1000 amostras, paramos aqui.
            if len(valid_time_gaps) >= MAX_SAMPLES_PER_DATASET:
                break

            current_timestamp, _, current_model = logs[i]
            prev_timestamp, _, _ = logs[i-1]
            
            time_diff_seconds = (current_timestamp - prev_timestamp).total_seconds()
            
            # Filtra tempos irreais (computador desligado/pausa longa)
            if time_diff_seconds > MAX_GAP_SECONDS:
                continue 
                
            valid_time_gaps.append(time_diff_seconds)
            models_used.append(current_model)
            
        # Calcula as estatísticas se tivermos dados
        if valid_time_gaps:
            num_samples = len(valid_time_gaps)
            total_time_seconds = sum(valid_time_gaps)
            average_time_seconds = statistics.mean(valid_time_gaps)
            total_hours = total_time_seconds / 3600
            
            # Encontra o modelo mais frequente (moda)
            most_common_model = Counter(models_used).most_common(1)[0][0]

            print(f"   -> Amostras Válidas: {num_samples}")
            print(f"   -> Modelo Principal: {most_common_model}")
            print(f"   -> Tempo Médio: {average_time_seconds:.2f} segundos/doc")
            print(f"   -> Tempo Total: {total_hours:.2f} horas")

            summary_results.append({
                "Dataset": dataset_name,
                "Docs_Analyzed": num_samples,
                "Most_Used_Model": most_common_model, # Nova Coluna
                "Average_Time_Sec": round(average_time_seconds, 2),
                "Total_Time_Hours": round(total_hours, 4),
                "Total_Time_Minutes": round(total_time_seconds / 60, 2)
            })
        else:
            print("   -> Nenhuma amostra de tempo válida encontrada.")

    # Salva o resumo em CSV
    if summary_results:
        try:
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=summary_results[0].keys())
                writer.writeheader()
                writer.writerows(summary_results)
            print(f"\n🎉 Resumo de tempo e modelos salvo em '{OUTPUT_FILE}'.")
        except Exception as e:
            print(f"\n❌ ERRO ao salvar o arquivo: {e}")
    else:
        print("\nNenhum resultado para salvar.")

if __name__ == "__main__":
    analyze_log_times_summary()