import os
import json
from genson import SchemaBuilder



def generate_schema(rawJsonDir, processedSchemasDir):
    
    """ Reads all the files in the rawJsonDir and 
        generates a schema for each file
        then saves the schema in the processedSchemasDir"""
        
        
    print("Generating schemas...")
    
    if not os.path.exists(processedSchemasDir):
        os.makedirs(processedSchemasDir)
        print(f"Created directory: {processedSchemasDir}")
    jsonFiles = [f for f in os.listdir(rawJsonDir) if f.endswith('.json')]
    if not jsonFiles:
        print("No JSON files found in the rawJsonDir.")
        return
    
    print(f"Found {len(jsonFiles)} JSON files in {rawJsonDir}.")
    
    for jsonFile in jsonFiles:
        entryPath = os.path.join(rawJsonDir, jsonFile)
        outputName = jsonFile.replace('.json', '.schema.json')
        outputPath = os.path.join(processedSchemasDir, outputName)
        
        try:
            with open(entryPath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                builder = SchemaBuilder()
                builder.add_object(data)
                schema = builder.to_schema()
            
            with open(outputPath, 'w',encoding='utf-8') as outputFile:
                json.dump(schema, outputFile, indent=4)
                
            print(f"Schema generated and saved to {outputPath}")
    
        except Exception as e:
            print(f"An error occurred while processing {entryPath}: {e}")
    

#Path to folders
rawJsonDir = "../datasets/rawJson"
processedSchemasDir = "../datasets/processedSchemas"

if __name__ == "__main__":
    generate_schema(rawJsonDir, processedSchemasDir)
    print("Schema generation completed.")
