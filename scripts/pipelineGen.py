import os
import subprocess
import zipfile
import shutil
import csv
import io

# --- Configuration ---
DATASETS_DIR = '../datasets/'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson/')
TEMP_DOWNLOADS_DIR = os.path.join(DATASETS_DIR, 'temp_downloads/')
DOWNLOAD_LOG_PATH = os.path.join(DATASETS_DIR, 'download_log.txt')

SEARCH_TERM = "json dataset"  # Term to search for on Kaggle
NUM_DATASETS_TO_DOWNLOAD = 10 # How many of the top datasets you want to download

# --- Schema Generator Script ---
# Import the function from the other script to call it at the end


def load_processed_datasets_log():
    """Loads the set of already processed dataset references from the log file."""
    if not os.path.exists(DOWNLOAD_LOG_PATH):
        return set()
    with open(DOWNLOAD_LOG_PATH, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def log_processed_dataset(dataset_ref):
    """Appends a newly processed dataset reference to the log file."""
    with open(DOWNLOAD_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{dataset_ref}\n")

def search_kaggle_datasets(search_term, limit):
    """Searches Kaggle for datasets and returns a list of references."""
    print(f"Searching for the top {limit} relevant datasets for '{search_term}'...")
    
    command = [
        "kaggle", "datasets", "list",
        "--search", search_term,
        "--sort-by", "votes",
        "--csv"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        csv_file = io.StringIO(result.stdout)
        reader = csv.reader(csv_file)
        next(reader)  # Skip header
        
        refs = [row[0] for row in reader]
        return refs[:limit]
        
    except subprocess.CalledProcessError as e:
        print(f"Error searching Kaggle datasets: {e.stderr}")
        return []
    except FileNotFoundError:
        print("Error: 'kaggle' command not found. Please ensure the Kaggle API is installed and in your system's PATH.")
        return []

def download_and_process_dataset(dataset_ref):
    """Downloads a dataset, unzips it, and moves any new JSON files."""
    print(f"\nProcessing dataset: {dataset_ref}...")
    
    if os.path.exists(TEMP_DOWNLOADS_DIR):
        shutil.rmtree(TEMP_DOWNLOADS_DIR)
    os.makedirs(TEMP_DOWNLOADS_DIR)

    download_command = [
        "kaggle", "datasets", "download",
        "-d", dataset_ref,
        "-p", TEMP_DOWNLOADS_DIR,
        "--unzip"
    ]
    
    try:
        subprocess.run(download_command, check=True, capture_output=True, text=True)
        print(f"  > Download and unzip successful for {dataset_ref}.")
        
        moved_files_count = 0
        for root, _, files in os.walk(TEMP_DOWNLOADS_DIR):
            for name in files:
                if name.endswith('.json'):
                    source_path = os.path.join(root, name)
                    destination_path = os.path.join(RAW_JSON_DIR, name)
                    
                    # Check if the file already exists in the destination
                    if not os.path.exists(destination_path):
                        shutil.move(source_path, destination_path)
                        moved_files_count += 1
                    else:
                        print(f"  - File '{name}' already exists. Skipping.")
        
        if moved_files_count > 0:
            print(f"  > Moved {moved_files_count} new .json file(s) to '{RAW_JSON_DIR}'.")
            # Log only if new files were actually added
            log_processed_dataset(dataset_ref)
        else:
            print("  > No new JSON files found to move.")
        
    except subprocess.CalledProcessError as e:
        print(f"  > Error downloading dataset {dataset_ref}: {e.stderr}")
    finally:
        if os.path.exists(TEMP_DOWNLOADS_DIR):
            shutil.rmtree(TEMP_DOWNLOADS_DIR)

def main():
    """Main function to orchestrate the entire pipeline."""
    os.makedirs(RAW_JSON_DIR, exist_ok=True)
    
    # Load the log of datasets that have already been processed
    processed_datasets = load_processed_datasets_log()
    print(f"Found {len(processed_datasets)} previously processed datasets in the log.")
    
    # Search for datasets on Kaggle
    dataset_refs = search_kaggle_datasets(SEARCH_TERM, NUM_DATASETS_TO_DOWNLOAD)
    
    if not dataset_refs:
        print("No datasets found or an error occurred during search. Exiting.")
        return
        
    print(f"\nTop datasets found: {dataset_refs}")
    
    # Download and process each dataset if it's not in the log
    for ref in dataset_refs:
        if ref not in processed_datasets:
            download_and_process_dataset(ref)
        else:
            print(f"\nSkipping '{ref}' as it's marked as processed in the log.")
            
    print("\n----------------------------------------------------")
    print("Data acquisition phase complete.")
if __name__ == '__main__':
    main()