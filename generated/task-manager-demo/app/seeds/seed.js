const { query, closePool } = require('../config/database');
const User = require('../models/User');
const Project = require('../models/Project');
const Task = require('../models/Task');

async function seed() {
  const db = { query };
  const userModel = new User(db);
  const projectModel = new Project(db);
  const taskModel = new Task(db);

  // Create tables
  await userModel.createTable();
  await projectModel.createTable();
  await taskModel.createTable();

  // Seed users
  const user1Id = await userModel.create({
    username: 'admin', email: 'admin@example.com',
    password: 'password123', display_name: 'Admin User',
  });
  const user2Id = await userModel.create({
    username: 'tanaka', email: 'tanaka@example.com',
    password: 'password123', display_name: 'Tanaka Taro',
  });
  const user3Id = await userModel.create({
    username: 'suzuki', email: 'suzuki@example.com',
    password: 'password123', display_name: 'Suzuki Hanako',
  });

  // Seed projects
  const proj1Id = await projectModel.create({
    name: 'Website Redesign', description: 'Redesign the company website with modern UI', owner_id: user1Id,
  });
  const proj2Id = await projectModel.create({
    name: 'Mobile App Development', description: 'Build a cross-platform mobile application', owner_id: user2Id,
  });

  // Seed tasks
  await taskModel.create({ title: 'Design mockups', description: 'Create wireframes and mockups for homepage', status: 'done', priority: 'high', project_id: proj1Id, assignee_id: user3Id, creator_id: user1Id });
  await taskModel.create({ title: 'Implement header component', description: 'Build responsive header with navigation', status: 'in_progress', priority: 'high', project_id: proj1Id, assignee_id: user2Id, creator_id: user1Id });
  await taskModel.create({ title: 'Setup CI/CD pipeline', description: 'Configure automated build and deployment', status: 'todo', priority: 'medium', project_id: proj1Id, assignee_id: user1Id, creator_id: user1Id });
  await taskModel.create({ title: 'API design', description: 'Design REST API endpoints for mobile app', status: 'in_progress', priority: 'high', project_id: proj2Id, assignee_id: user2Id, creator_id: user2Id });
  await taskModel.create({ title: 'User authentication', description: 'Implement login and registration flow', status: 'todo', priority: 'high', project_id: proj2Id, assignee_id: user3Id, creator_id: user2Id });
  await taskModel.create({ title: 'Database schema', description: 'Design and implement database schema', status: 'done', priority: 'medium', project_id: proj2Id, assignee_id: user2Id, creator_id: user2Id });

  console.log('Seed data inserted successfully');
  await closePool();
}

seed().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
