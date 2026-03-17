const bcrypt = require('bcryptjs');

async function seedData() {
  const { User, Project, Ticket } = require('./index');

  // Idempotent: check if data already exists
  const userCount = await User.count();
  if (userCount > 0) {
    return;
  }

  // Create users (password hashing handled by model hook)
  const admin = await User.create({
    username: 'admin',
    password: 'admin123',
    displayName: 'Admin User',
    role: 'admin'
  });

  const tanaka = await User.create({
    username: 'tanaka',
    password: 'tanaka123',
    displayName: 'Tanaka Taro',
    role: 'member'
  });

  const suzuki = await User.create({
    username: 'suzuki',
    password: 'suzuki123',
    displayName: 'Suzuki Hanako',
    role: 'member'
  });

  // Create projects
  const projectA = await Project.create({
    name: 'Project Alpha',
    description: 'Main product development project',
    status: 'active'
  });

  const projectB = await Project.create({
    name: 'Project Beta',
    description: 'Internal tools project',
    status: 'active'
  });

  // Create tickets
  await Ticket.create({
    title: 'Implement login page',
    description: 'Create login page with username/password form',
    status: 'resolved',
    priority: 'high',
    projectId: projectA.id,
    assigneeId: tanaka.id,
    creatorId: admin.id
  });

  await Ticket.create({
    title: 'Fix navigation bug',
    description: 'Navigation bar does not collapse on mobile',
    status: 'open',
    priority: 'medium',
    projectId: projectA.id,
    assigneeId: suzuki.id,
    creatorId: tanaka.id
  });

  await Ticket.create({
    title: 'Add search functionality',
    description: 'Implement ticket search by title and description',
    status: 'in_progress',
    priority: 'medium',
    projectId: projectA.id,
    assigneeId: tanaka.id,
    creatorId: admin.id
  });

  await Ticket.create({
    title: 'Setup CI/CD pipeline',
    description: 'Configure automated build and deployment',
    status: 'open',
    priority: 'high',
    projectId: projectB.id,
    assigneeId: suzuki.id,
    creatorId: admin.id
  });

  await Ticket.create({
    title: 'Write API documentation',
    description: 'Document all REST endpoints',
    status: 'open',
    priority: 'low',
    projectId: projectB.id,
    assigneeId: null,
    creatorId: tanaka.id
  });

  console.log('Seed data created successfully');
}

module.exports = { seedData };
