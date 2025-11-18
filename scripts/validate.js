import { createReadStream, createWriteStream, existsSync, promises as fs } from 'fs';
import path from 'path';
import Ajv from 'ajv';

import StreamChain from 'stream-chain';
const { chain } = StreamChain;
import StreamJsonParser from 'stream-json';
const { parser } = StreamJsonParser;
import StreamArrayPkg from 'stream-json/streamers/StreamArray.js';
const { streamArray } = StreamArrayPkg;
import JsonlParserPkg from 'stream-json/jsonl/Parser.js';
const { parser: JsonlParser } = JsonlParserPkg;

// --- CONFIGURAÇÕES ---
const MASTER_SCHEMA_DIR = '.'; 
const ORIGINAL_DATA_DIR = 'datasets/';
const LOG_FILE = 'validation_original_report.csv';
const SUMMARY_LOG_FILE = 'validation_summary_report.csv';
const DATASET_SUMMARY_FILE = 'validation_dataset_summary.csv'; 
// ---------------------

let summaryLogStream;
let datasetSummaryStream;

async function main() {
    console.log('--- Iniciando Validação de STRESS com Arquivos Originais ---');
    
    const logStream = createWriteStream(LOG_FILE, { encoding: 'utf-8' });
    logStream.write('dataset,document_index,error_path,message,params\n');
    console.log(` Relatório de erros será salvo em: ${LOG_FILE}`);

    summaryLogStream = createWriteStream(SUMMARY_LOG_FILE, { encoding: 'utf-8' });
    summaryLogStream.write('Dataset,Total_Documentos,Aprovados,Reprovados,Taxa_Sucesso_Percentual\n');
    console.log(` Relatório de resumo será salvo em: ${SUMMARY_LOG_FILE}`);

    datasetSummaryStream = createWriteStream(DATASET_SUMMARY_FILE, { encoding: 'utf-8' });
    datasetSummaryStream.write('dataset,total_documentos,aprovados,reprovados,taxa_sucesso_percentual\n');
    console.log(` Resumo simplificado (logs do console) será salvo em: ${DATASET_SUMMARY_FILE}`);

    let masterSchemas = [];
    try {
        masterSchemas = (await fs.readdir(MASTER_SCHEMA_DIR))
            .filter(file => file.endsWith('_master_schema.json'));
        console.log(` Schemas mestres encontrados: ${masterSchemas.join(', ')}`);
    } catch (err) {
        console.error(` ERRO: Não foi possível ler o diretório de schemas em '${MASTER_SCHEMA_DIR}'.`);
        return;
    }

    for (const schemaFile of masterSchemas) {
        const datasetName = schemaFile.replace('_master_schema.json', '');
        await validateDataset(datasetName, schemaFile, logStream);
    }

    logStream.end();
    summaryLogStream.end();
    datasetSummaryStream.end();

    console.log('\n--- Processo de Validação Concluído ---');
}

async function validateDataset(datasetName, schemaFile, logStream) {
    console.log(`\n--- Validando Dataset: ${datasetName} ---`);

    const schemaPath = path.join(MASTER_SCHEMA_DIR, schemaFile);
    let originalDataName = datasetName;
    
    if (datasetName.startsWith('dataset_5MB_')) {
        originalDataName = 'dataset_5MB';
        console.log(`  -> Detectado dataset sintético variado. Usando fonte de dados: ${originalDataName}.jsonl`);
    }
    
    let dataFilePath = path.join(ORIGINAL_DATA_DIR, `${originalDataName}.json`);
    if (!existsSync(dataFilePath)) {
        dataFilePath = path.join(ORIGINAL_DATA_DIR, `${originalDataName}.jsonl`);
        if (!existsSync(dataFilePath)) {
            console.warn(`    Aviso: Arquivo de dados original '${originalDataName}.json[l]' não encontrado em '${ORIGINAL_DATA_DIR}'. Pulando dataset.`);
            return;
        }
    }

    const ajv = new Ajv({ strict: false });
    let validate;
    try {
        const schema = JSON.parse(await fs.readFile(schemaPath, 'utf-8'));
        validate = ajv.compile(schema);
        console.log("   Schema mestre carregado e compilado com sucesso.");
    } catch (err) {
        console.error(`   ERRO: Falha ao carregar ou compilar o schema '${schemaPath}'. Erro: ${err.message}`);
        return;
    }

    let fileFormat = 'unknown';
    try {
        const buffer = Buffer.alloc(100);
        const fd = await fs.open(dataFilePath, 'r');
        await fd.read(buffer, 0, 100, 0);
        await fd.close();
        
        const chunk = buffer.toString('utf-8').trim();
        
        if (chunk.startsWith('[')) fileFormat = 'json_array';
        else if (chunk.startsWith('{')) fileFormat = 'json_lines';
        
    } catch (e) {
        console.error(`   ERRO: Não foi possível ler o arquivo de dados ${dataFilePath}.`);
        console.error(`     Erro Detalhado: ${e.message}`);
        return;
    }

    let streamer;
    const fileStream = createReadStream(dataFilePath, { encoding: 'utf-8' });

    if (fileFormat === 'json_array') {
        console.log("  Formato detectado: JSON Array. Usando 'streamArray'...");
        streamer = chain([ 
            fileStream, 
            parser({stripBom: true}), 
            streamArray() 
        ]);
    } else if (fileFormat === 'json_lines') {
        console.log("  Formato detectado: JSON Lines. Usando 'JsonlParser'...");
        streamer = chain([ 
            fileStream, 
            JsonlParser({stripBom: true}) 
        ]);
    } else {
        console.warn(`    Aviso: Formato de dados desconhecido em ${dataFilePath}. Pulando.`);
        return;
    }

    let passedCount = 0;
    let failedCount = 0;
    let docIndex = 0;

    return new Promise((resolve, reject) => {
        streamer.on('data', ({ key, value }) => {
            docIndex++;
            const data = value;
            
            try {
                const valid = validate(data);
                if (valid) {
                    passedCount++;
                } else {
                    failedCount++;
                    for (const err of validate.errors) {
                        const errorPath = err.instancePath || 'root';
                        const message = (err.message || '').replace(/"/g, "'");
                        const params = JSON.stringify(err.params).replace(/"/g, "'");
                        logStream.write(`${datasetName},doc_${docIndex},${errorPath},${message},${params}\n`);
                    }
                }
            } catch (err) {
                failedCount++;
                logStream.write(`${datasetName},doc_${docIndex},validation_crash,Erro ao validar,${err.message.replace(/"/g, "'")}\n`);
            }
            
            if (docIndex % 5000 === 0) {
                 process.stdout.write(`      -> Documentos processados: ${docIndex} (Falhas: ${failedCount})\r`);
            }
        });

        streamer.on('end', () => {
            const total = passedCount + failedCount;
            const successRate = total > 0 ? (passedCount / total * 100).toFixed(2) : "N/A";

            // --- Logs do resumo ---
            console.log(`\n  --- Resumo para ${datasetName} ---`);
            console.log(`  Total de Documentos no arquivo: ${total}`);
            console.log(`   Aprovados: ${passedCount}`);
            console.log(`   Reprovados: ${failedCount}`);
            console.log(`  Taxa de Sucesso: ${successRate}%`);

            // --- Salva também em CSV separado ---
            datasetSummaryStream.write(`${datasetName},${total},${passedCount},${failedCount},${successRate}\n`);

            // Mantém o log completo também
            summaryLogStream.write(`${datasetName},${total},${passedCount},${failedCount},${successRate}\n`);

            resolve();
        });

        streamer.on('error', (err) => {
            console.error(`   ERRO durante o streaming: ${err.message}`);
            reject(err);
        });
    });
}

// Inicia a execução do script
main().catch(err => {
    console.error("Um erro fatal ocorreu:", err);
});
