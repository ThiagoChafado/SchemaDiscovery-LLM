const fs = require('fs');
const path = require('path');
const { faker } = require('@faker-js/faker');

//Description
/**
 * Este script gera 10.000 arquivos JSON variados e levemente "sujos" (com valores nulos ou campos omitidos)
 * usando a biblioteca Faker.js. Cada arquivo contém um objeto JSON representando diferentes tipos de dados
 * como pessoa, produto, local, transação e evento.
 * Os arquivos são salvos na pasta `jsonObjects` dentro do diretório do script.
 * Para executar o script, use o comando: `node scripts/getJson.js`
 * Certifique-se de ter a biblioteca Faker.js instalada: `npm install @faker-js/faker`
 * Cada objeto gerado pode conter campos com valores nulos ou campos omitidos para simular dados "sujos".
 */

//Pega os geradores de objetos do arquivo Objects.js 
const { generatePerson, generateProduct,
    generateLocation, 
    generateTransaction, 
    generateEvent 
} = require('./Objects.js');

//Geradores possíveis de objetos JSON
const generators = [generatePerson, generateProduct, generateLocation, generateTransaction, generateEvent];



// Pasta de saída
const outputDir = path.join(__dirname, 'jsonObjects');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

let fileCounter = 1;



// Gera N arquivos com dados variados
async function generateRandomJsonFiles(quantity = 10000) {
    for (let i = 0; i < quantity; i++) {
        const generator = faker.helpers.arrayElement(generators);
        const jsonObject = generator();

        // Remove campos com `undefined`
        Object.keys(jsonObject).forEach(k => {
            if (jsonObject[k] === undefined) delete jsonObject[k];
        });

        const filePath = path.join(outputDir, `data_${fileCounter++}.json`);
        await fs.promises.writeFile(filePath, JSON.stringify(jsonObject, null, 2));
        if (i % 500 === 0) console.log(`Gerados ${i} arquivos...`);
    }

    console.log(`${quantity} arquivos JSON variados e levemente sujos foram gerados.`);
}

generateRandomJsonFiles(10); 
