const bcrypt = require('bcryptjs');

class User {
  constructor(db) {
    this.db = db;
  }

  async createTable() {
    await this.db.query(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(255) NOT NULL UNIQUE,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        display_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  async create({ username, email, password, display_name }) {
    const password_hash = await bcrypt.hash(password, 10);
    const result = await this.db.query(
      'INSERT INTO users (username, email, password_hash, display_name) VALUES (?, ?, ?, ?)',
      [username, email, password_hash, display_name || username]
    );
    return result.insertId || result;
  }

  async findByUsername(username) {
    const rows = await this.db.query('SELECT * FROM users WHERE username = ?', [username]);
    return rows[0] || null;
  }

  async findById(id) {
    const rows = await this.db.query('SELECT * FROM users WHERE id = ?', [id]);
    return rows[0] || null;
  }

  async findAll() {
    return this.db.query('SELECT id, username, email, display_name, created_at FROM users');
  }

  async verifyPassword(plainPassword, hashedPassword) {
    return bcrypt.compare(plainPassword, hashedPassword);
  }
}

module.exports = User;
