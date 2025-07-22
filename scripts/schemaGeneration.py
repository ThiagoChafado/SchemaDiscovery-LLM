# scripts/schemaGenerator.py

import os
import json
import csv
import csv
from genson import SchemaBuilder

# --- Configuration ---
DATASETS_DIR = '../datasets/'
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson/')
PROCESSED_SCHEMAS_DIR = os.path.join(DATASETS_DIR, 'processedSchemas/')
MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest.csv')

MAX_STANDARD_JSON_SIZE_MB = 500

def updateManifestFile():
    """
    Scans the processed schemas directory and creates an up-to-date manifest file.
    """
    print("\n----------------------------------------------------")
    print("Updating manifest.csv...")
    
    validPairs = []
# --- Configuration ---
DATASETS_DIR = 'datasets' # Nome base da pasta
RAW_JSON_DIR = os.path.join(DATASETS_DIR, 'rawJson')
PROCESSED_SCHEMAS_DIR = os.path.join(DATASETS_DIR, 'processedSchemas')
MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest.csv')
MAX_STANDARD_JSON_SIZE_MB = 500

def updateManifestFile():
    print("\n----------------------------------------------------")
    print("Updating manifest.csv...")
    
    validPairs = []
    
    if not os.path.exists(PROCESSED_SCHEMAS_DIR):
        print("Processed schemas directory not found. Manifest not created.")
    if not os.path.exists(PROCESSED_SCHEMAS_DIR):
        print("Processed schemas directory not found. Manifest not created.")
        return

    for schemaFilename in os.listdir(PROCESSED_SCHEMAS_DIR):
        if schemaFilename.endswith('.schema.json'):
            jsonFilename = schemaFilename.replace('.schema.json', '.json')
            jsonFilePath = os.path.join(RAW_JSON_DIR, jsonFilename)
            
            if os.path.exists(jsonFilePath):
                # --- ESTA É A CORREÇÃO CRÍTICA ---
                # Garante que o caminho completo seja salvo no manifesto
                relativeJsonPath = os.path.join(RAW_JSON_DIR, jsonFilename)
                relativeSchemaPath = os.path.join(PROCESSED_SCHEMAS_DIR, schemaFilename)
                
                validPairs.append({
                    'json_path': relativeJsonPath,
                    'schema_path': relativeSchemaPath
                })
    
    if not validPairs:
        print("No valid JSON/Schema pairs found. Manifest not created.")
        return
        
    try:
        with open(MANIFEST_PATH, 'w', newline='', encoding='utf-8') as f:
            fieldNames = ['json_path', 'schema_path']
            writer = csv.DictWriter(f, fieldnames=fieldNames)
            writer.writeheader()
            writer.writerows(validPairs)
        print(f"Manifest.csv updated successfully with {len(validPairs)} pairs.")
    except Exception as e:
        print(f"Error writing to manifest.csv: {e}")

def generateSchemasAutomatically():
    # Esta função continua a mesma
    print("Generating schemas with improved memory management...")
    os.makedirs(PROCESSED_SCHEMAS_DIR, exist_ok=True)
    jsonFiles = [f for f in os.listdir(RAW_JSON_DIR) if f.endswith('.json')]
    print(f"Found {len(jsonFiles)} JSON files in {RAW_JSON_DIR}.")

    for filename in jsonFiles:
        inputPath = os.path.join(RAW_JSON_DIR, filename)
        outputFilename = filename.replace('.json', '.schema.json')
        outputPath = os.path.join(PROCESSED_SCHEMAS_DIR, outputFilename)
        
        if os.path.exists(outputPath):
            print(f"Schema for '{filename}' already exists. Skipping.")
            continue
            
        builder = SchemaBuilder()
        linesProcessed = 0
        fileProcessed = False

        try:
            with open(inputPath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        jsonObject = json.loads(line)
                        builder.add_object(jsonObject)
                        linesProcessed += 1
            if linesProcessed > 0: fileProcessed = True
        except json.JSONDecodeError:
            fileSizeMb = os.path.getsize(inputPath) / (1024 * 1024)
            if fileSizeMb > MAX_STANDARD_JSON_SIZE_MB:
                print(f"Warning: Skipping '{filename}' ({fileSizeMb:.2f}MB). File is too large.")
                continue
            try:
                with open(inputPath, 'r', encoding='utf-8') as f:
                    jsonObject = json.load(f)
                    builder.add_object(jsonObject)
                    linesProcessed = 1
                    fileProcessed = True
            except Exception as e:
                print(f"Error: Could not parse '{filename}' as a standard JSON. Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with '{filename}': {e}")

        if fileProcessed and linesProcessed > 0:
            generatedSchema = builder.to_schema()
            with open(outputPath, 'w', encoding='utf-8') as f:
                json.dump(generatedSchema, f, indent=4)
            print(f"Schema generated for '{filename}' and saved to '{outputFilename}'")

    print("\nSchema generation finished!")
    updateManifestFile()

if __name__ == '__main__':
    generateSchemasAutomatically()