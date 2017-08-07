const path = require('path');
const movies_dir = path.resolve(__dirname, '../../../../filme/');

// for Development:
//const movies_dir = path.resolve(__dirname, '../filme/');

const knex = require('knex')({
    client: 'sqlite3',
    connection: {
        filename: movies_dir + '/lines.db'
    }
});

exports.movies_dir = movies_dir;
exports.knex = knex;
