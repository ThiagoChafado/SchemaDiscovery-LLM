import os
import subprocess
import shutil
import csv
import io
import re

# --- Configuration ---
DATASETS_DIR = '../datasets/'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson/')
TEMP_DOWNLOADS_DIR = os.path.join(DATASETS_DIR, 'tempDowloads/')
DOWNLOAD_LOG_PATH = os.path.join(DATASETS_DIR, 'dowloadLog.txt')

SEARCH_TERMS = [
    "government json api",
    "scientific data json",
    "product catalog json",
    "financial data json",
    "nested json",
    "geolocation json"
]
DATASETS_PER_TERM = 5
MAX_DATASET_SIZE_MB = 200

def parseSizeToMb(sizeStr):
    """Converts Kaggle's size string (e.g., '100KB', '50MB', '2GB') to megabytes."""
    if not sizeStr:
        return 0
    sizeStr = sizeStr.upper()
    num_match = re.findall(r'[\d\.]+', sizeStr)
    if not num_match:
        return 0
    num = float(num_match[0])
    
    if "G" in sizeStr:
        return num * 1024
    if "M" in sizeStr:
        return num
    if "K" in sizeStr:
        return num / 1024
    return num / (1024 * 1024)

def loadProcessedDataLog():
    """Loads the set of already processed dataset references from the log file."""
    if not os.path.exists(DOWNLOAD_LOG_PATH):
        return set()
    with open(DOWNLOAD_LOG_PATH, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def logProcessedData(datasetRef):
    """Appends a newly processed dataset reference to the log file."""
    with open(DOWNLOAD_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{datasetRef}\n")

def searchKaggleDatasets(searchTerm, sizeLimitMb):
    """Searches Kaggle for small datasets and returns a list of references."""
    print(f"\nSearching for datasets matching '{searchTerm}' (smaller than {sizeLimitMb}MB)...")
    
    command = [
        "kaggle", "datasets", "list",
        "--search", searchTerm,
        "--csv"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        csvFile = io.StringIO(result.stdout)
        reader = csv.reader(csvFile)
        header = next(reader)
        refIndex = header.index('ref')
        sizeIndex = header.index('size')
        
        filteredRefs = []
        for row in reader:
            ref = row[refIndex]
            sizeStr = row[sizeIndex]
            sizeMb = parseSizeToMb(sizeStr)
            
            if sizeMb <= sizeLimitMb:
                filteredRefs.append(ref)
        
        print(f"  > Found {len(filteredRefs)} datasets under the size limit.")
        return filteredRefs
        
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"  > Error during Kaggle search: {e}")
        return []

def downloadAndProcessDataset(datasetRef):
    """Downloads a dataset, unzips it, and moves any new JSON files."""
    print(f"\nProcessing dataset: {datasetRef}...")
    if os.path.exists(TEMP_DOWNLOADS_DIR): shutil.rmtree(TEMP_DOWNLOADS_DIR)
    os.makedirs(TEMP_DOWNLOADS_DIR)
    downloadCommand = ["kaggle", "datasets", "download", "-d", datasetRef, "-p", TEMP_DOWNLOADS_DIR, "--unzip"]
    try:
        subprocess.run(downloadCommand, check=True, capture_output=True, text=True)
        print(f"  > Download and unzip successful for {datasetRef}.")
        movedFilesCount = 0
        for root, _, files in os.walk(TEMP_DOWNLOADS_DIR):
            for name in files:
                if name.endswith('.json'):
                    sourcePath = os.path.join(root, name)
                    destinationPath = os.path.join(RAW_JSON_DIR, name)
                    if not os.path.exists(destinationPath):
                        shutil.move(sourcePath, destinationPath)
                        movedFilesCount += 1
                    else:
                        print(f"  - File '{name}' already exists. Skipping.")
        if movedFilesCount > 0:
            print(f"  > Moved {movedFilesCount} new .json file(s) to '{RAW_JSON_DIR}'.")
            logProcessedData(datasetRef)
        else:
            print("  > No new JSON files found to move.")
    except subprocess.CalledProcessError as e:
        print(f"  > Error downloading dataset {datasetRef}: {e.stderr}")
    finally:
        if os.path.exists(TEMP_DOWNLOADS_DIR): shutil.rmtree(TEMP_DOWNLOADS_DIR)

def main():
    """Main function to orchestrate the refined acquisition pipeline."""
    os.makedirs(RAW_JSON_DIR, exist_ok=True)
    
    processedDatasets = loadProcessedDataLog()
    print(f"Found {len(processedDatasets)} previously processed datasets in the log.")
    
    allNewDatasetsToProcess = []
    for term in SEARCH_TERMS:
        datasetRefs = searchKaggleDatasets(term, MAX_DATASET_SIZE_MB)
        
        newRefsForTerm = 0
        for ref in datasetRefs:
            if newRefsForTerm >= DATASETS_PER_TERM:
                break
            if ref not in processedDatasets and ref not in allNewDatasetsToProcess:
                allNewDatasetsToProcess.append(ref)
                newRefsForTerm += 1

    if not allNewDatasetsToProcess:
        print("\nNo new datasets to download based on the specified criteria. Exiting.")
        return

    print(f"\nFound a total of {len(allNewDatasetsToProcess)} new, unique datasets to process.")
    
    for ref in allNewDatasetsToProcess:
        downloadAndProcessDataset(ref)
            
    print("\n----------------------------------------------------")
    print("Data acquisition phase complete.")

if __name__ == '__main__':
    main()