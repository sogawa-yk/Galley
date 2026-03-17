class Task {
  constructor(db) {
    this.db = db;
  }

  async createTable() {
    await this.db.query(`
      CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'todo',
        priority VARCHAR(50) DEFAULT 'medium',
        project_id INTEGER,
        assignee_id INTEGER,
        creator_id INTEGER NOT NULL,
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (assignee_id) REFERENCES users(id),
        FOREIGN KEY (creator_id) REFERENCES users(id)
      )
    `);
  }

  async create({ title, description, status, priority, project_id, assignee_id, creator_id, due_date }) {
    const result = await this.db.query(
      `INSERT INTO tasks (title, description, status, priority, project_id, assignee_id, creator_id, due_date)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [title, description || '', status || 'todo', priority || 'medium',
       project_id || null, assignee_id || null, creator_id, due_date || null]
    );
    return result.insertId || result;
  }

  async findAll(filters = {}) {
    let sql = `
      SELECT t.*,
             u1.display_name as assignee_name,
             u2.display_name as creator_name,
             p.name as project_name
      FROM tasks t
      LEFT JOIN users u1 ON t.assignee_id = u1.id
      LEFT JOIN users u2 ON t.creator_id = u2.id
      LEFT JOIN projects p ON t.project_id = p.id
      WHERE 1=1
    `;
    const params = [];

    if (filters.project_id) {
      sql += ' AND t.project_id = ?';
      params.push(filters.project_id);
    }
    if (filters.assignee_id) {
      sql += ' AND t.assignee_id = ?';
      params.push(filters.assignee_id);
    }
    if (filters.status) {
      sql += ' AND t.status = ?';
      params.push(filters.status);
    }

    sql += ' ORDER BY t.created_at DESC';
    return this.db.query(sql, params);
  }

  async findById(id) {
    const rows = await this.db.query(`
      SELECT t.*,
             u1.display_name as assignee_name,
             u2.display_name as creator_name,
             p.name as project_name
      FROM tasks t
      LEFT JOIN users u1 ON t.assignee_id = u1.id
      LEFT JOIN users u2 ON t.creator_id = u2.id
      LEFT JOIN projects p ON t.project_id = p.id
      WHERE t.id = ?
    `, [id]);
    return rows[0] || null;
  }

  async update(id, { title, description, status, priority, project_id, assignee_id, due_date }) {
    await this.db.query(
      `UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?,
       project_id = ?, assignee_id = ?, due_date = ?, updated_at = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [title, description, status, priority, project_id || null, assignee_id || null, due_date || null, id]
    );
  }

  async delete(id) {
    await this.db.query('DELETE FROM tasks WHERE id = ?', [id]);
  }

  async getStatusCounts() {
    return this.db.query(
      'SELECT status, COUNT(*) as count FROM tasks GROUP BY status'
    );
  }
}

module.exports = Task;
