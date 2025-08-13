const fs = require('fs');
const path = require('path');
const { faker } = require('@faker-js/faker');

/**
 * 
 * Este módulo exporta funções para gerar objetos JSON variados e levemente "sujos" (com valores nulos ou campos omitidos)
 * usando a biblioteca Faker.js. Cada função gera um objeto representando diferentes tipos de dados
 * como pessoa, produto, local, transação e evento.
 */



// Gera um objeto do tipo pessoa
function generatePerson() {
    return {
        type: "person",
        id: faker.string.numeric(),
        name: maybe(faker.person.fullName()),
        email: maybe(faker.internet.email()),
        phone: maybe(faker.phone.number()),
        age: maybe(faker.number.int({ min: 18, max: 90 })),
        tags: maybe([faker.word.adjective(), faker.word.noun(), faker.word.verb()]),
        address: maybe({
            street: maybe(faker.location.street()),
            city: maybe(faker.location.city()),
            zip: maybe(faker.location.zipCode())
        })
    };
}

// Gera um objeto do tipo produto
function generateProduct() {
    return {
        type: "product",
        sku: faker.string.uuid(),
        name: maybe(faker.commerce.productName()),
        category: maybe(faker.commerce.department()),
        price: maybe(parseFloat(faker.commerce.price())),
        available: maybe(faker.datatype.boolean()),
        tags: maybe([faker.commerce.productAdjective(), faker.commerce.productMaterial()])
    };
}

// Gera um objeto do tipo local
function generateLocation() {
    return {
        type: "location",
        id: faker.string.uuid(),
        name: maybe(faker.location.city()),
        latitude: maybe(faker.location.latitude()),
        longitude: maybe(faker.location.longitude()),
        address: maybe({
            street: maybe(faker.location.streetAddress()),
            country: maybe(faker.location.country()),
        }),
        phones: maybe([
            faker.phone.number(),
            Math.random() > 0.5 ? faker.phone.number() : null
        ])
    };
}

// Gera um objeto do tipo transação
function generateTransaction() {
    return {
        type: "transaction",
        transactionId: faker.string.uuid(),
        amount: maybe(parseFloat(faker.finance.amount())),
        currency: maybe(faker.finance.currencyCode()),
        date: maybe(faker.date.recent().toISOString()),
        description: maybe(faker.finance.transactionDescription()),
        status: maybe(faker.helpers.arrayElement(['completed', 'pending', 'failed']))
    };
}

// Gera um objeto do tipo evento
function generateEvent() {
    return {
        type: "event",
        name: maybe(faker.word.words({ count: { min: 1, max: 3 } })),
        timestamp: maybe(faker.date.past().toISOString()),
        participants: maybe([
            faker.person.fullName(),
            faker.person.fullName()
        ]),
        location: maybe(faker.location.city()),
        metadata: maybe({
            source: faker.internet.domainName(),
            ip: faker.internet.ip()
        })
    };
}

// Função utilitária para aplicar valores nulos ou omissões
function maybe(value) {
    const r = Math.random();
    if (r < 0.1) return null;      // 10% chance de null
    if (r < 0.2) return undefined; // 10% chance de campo omitido
    return value;
}

module.exports = {
    generatePerson,
    generateProduct,
    generateLocation,
    generateTransaction,
    generateEvent
};
