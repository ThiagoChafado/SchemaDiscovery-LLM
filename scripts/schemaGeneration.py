import os
import json
from genson import SchemaBuilder

RAW_JSON_DIR = '../datasets/rawJson/'
PROCESSED_SCHEMAS_DIR = '../datasets/processedSchemas/'

def generateSchemasAutomatically():
    """
    Reads all .json files from the input directory line by line,
    generates a basic schema for each, and saves it to the output directory.
    This method is memory-efficient and handles JSON Lines format.
    """
    print("Generating schemas...")

    if not os.path.exists(PROCESSED_SCHEMAS_DIR):
        os.makedirs(PROCESSED_SCHEMAS_DIR)
        print(f"Output directory created at: {PROCESSED_SCHEMAS_DIR}")

    json_files = [f for f in os.listdir(RAW_JSON_DIR) if f.endswith('.json')]

    if not json_files:
        print("No .json files found in the input directory.")
        return

    print(f"Found {len(json_files)} JSON files in {RAW_JSON_DIR}.")

    for filename in json_files:
        input_path = os.path.join(RAW_JSON_DIR, filename)
        output_filename = filename.replace('.json', '.schema.json')
        output_path = os.path.join(PROCESSED_SCHEMAS_DIR, output_filename)

        # Create a new SchemaBuilder for each file
        builder = SchemaBuilder()
        lines_processed = 0
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                # Process the file line by line to save memory and handle JSON Lines
                for line in f:
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    try:
                        # json.loads() is for strings, json.load() is for file objects
                        json_object = json.loads(line)
                        builder.add_object(json_object)
                        lines_processed += 1
                    except json.JSONDecodeError:
                        # This handles files that might be a single, pretty-printed JSON object
                        # We try to parse the whole file at once if line-by-line fails
                        f.seek(0) # Go back to the start of the file
                        json_object = json.load(f)
                        builder.add_object(json_object)
                        lines_processed = 1
                        break # Exit the loop since the whole file is processed

            if lines_processed > 0:
                # Generate and save the final schema
                generated_schema = builder.to_schema()
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(generated_schema, f, indent=4)
                print(f"Schema generated for '{filename}' ({lines_processed} lines/objects processed) and saved to '{output_filename}'")
            else:
                print(f"Warning: No valid JSON objects found in '{filename}'. Schema not generated.")

        except Exception as e:
            print(f"An error occurred while processing {input_path}: {e}")

    print("\nSchema generation finished!")


if __name__ == '__main__':
    generateSchemasAutomatically()