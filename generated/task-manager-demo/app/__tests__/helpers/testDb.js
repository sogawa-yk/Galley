const Database = require('better-sqlite3');

function createTestDb() {
  const sqlite = new Database(':memory:');
  sqlite.pragma('journal_mode = WAL');
  sqlite.pragma('foreign_keys = ON');

  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      display_name TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS projects (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      owner_id INTEGER NOT NULL,
      status TEXT DEFAULT 'active',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (owner_id) REFERENCES users(id)
    )
  `);

  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT DEFAULT 'todo',
      priority TEXT DEFAULT 'medium',
      project_id INTEGER,
      assignee_id INTEGER,
      creator_id INTEGER NOT NULL,
      due_date TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (project_id) REFERENCES projects(id),
      FOREIGN KEY (assignee_id) REFERENCES users(id),
      FOREIGN KEY (creator_id) REFERENCES users(id)
    )
  `);

  const db = {
    query: async (sql, params = []) => {
      // Skip DDL statements (tables already created)
      if (/^\s*CREATE\s+TABLE/i.test(sql.trim())) {
        return [];
      }

      try {
        if (/^\s*(INSERT|UPDATE|DELETE)/i.test(sql.trim())) {
          const stmt = sqlite.prepare(sql);
          const result = stmt.run(...params);
          if (/^\s*INSERT/i.test(sql.trim())) {
            return { insertId: Number(result.lastInsertRowid) };
          }
          return { affectedRows: result.changes };
        } else {
          const stmt = sqlite.prepare(sql);
          return stmt.all(...params);
        }
      } catch (err) {
        throw err;
      }
    },
    close: () => {
      sqlite.close();
    },
    _sqlite: sqlite,
  };

  return db;
}

module.exports = { createTestDb };
