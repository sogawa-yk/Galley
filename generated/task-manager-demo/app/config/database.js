const mysql = require('mysql2/promise');

let pool = null;

function getPool() {
  if (!pool) {
    const connectionString = process.env.DB_CONNECTION_STRING;
    if (connectionString) {
      pool = mysql.createPool(connectionString);
    } else {
      pool = mysql.createPool({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '3306', 10),
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        database: process.env.DB_NAME || 'task_manager',
        waitForConnections: true,
        connectionLimit: 10,
      });
    }
  }
  return pool;
}

async function query(sql, params = []) {
  const p = getPool();
  const [rows] = await p.execute(sql, params);
  return rows;
}

async function closePool() {
  if (pool) {
    await pool.end();
    pool = null;
  }
}

module.exports = { getPool, query, closePool };
