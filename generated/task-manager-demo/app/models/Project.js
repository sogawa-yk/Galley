class Project {
  constructor(db) {
    this.db = db;
  }

  async createTable() {
    await this.db.query(`
      CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        owner_id INTEGER NOT NULL,
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(id)
      )
    `);
  }

  async create({ name, description, owner_id }) {
    const result = await this.db.query(
      'INSERT INTO projects (name, description, owner_id) VALUES (?, ?, ?)',
      [name, description || '', owner_id]
    );
    return result.insertId || result;
  }

  async findAll() {
    return this.db.query(`
      SELECT p.*, u.display_name as owner_name
      FROM projects p
      JOIN users u ON p.owner_id = u.id
      ORDER BY p.created_at DESC
    `);
  }

  async findById(id) {
    const rows = await this.db.query(`
      SELECT p.*, u.display_name as owner_name
      FROM projects p
      JOIN users u ON p.owner_id = u.id
      WHERE p.id = ?
    `, [id]);
    return rows[0] || null;
  }

  async update(id, { name, description, status }) {
    await this.db.query(
      'UPDATE projects SET name = ?, description = ?, status = ? WHERE id = ?',
      [name, description, status, id]
    );
  }

  async delete(id) {
    await this.db.query('DELETE FROM projects WHERE id = ?', [id]);
  }
}

module.exports = Project;
