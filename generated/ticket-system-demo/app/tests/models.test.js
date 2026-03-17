const { sequelize, User, Project, Ticket } = require('../models');
const { seedData } = require('../models/seed');

beforeAll(async () => {
  await sequelize.sync({ force: true });
  await seedData();
});

afterAll(async () => {
  await sequelize.close();
});

describe('User model', () => {
  test('should have seeded users', async () => {
    const users = await User.findAll();
    expect(users.length).toBe(3);
  });

  test('should hash password on creation', async () => {
    const user = await User.findOne({ where: { username: 'admin' } });
    expect(user.password).not.toBe('admin123');
    expect(user.password.length).toBeGreaterThan(20);
  });

  test('should validate correct password', async () => {
    const user = await User.findOne({ where: { username: 'admin' } });
    const isValid = await user.validatePassword('admin123');
    expect(isValid).toBe(true);
  });

  test('should reject incorrect password', async () => {
    const user = await User.findOne({ where: { username: 'admin' } });
    const isValid = await user.validatePassword('wrong');
    expect(isValid).toBe(false);
  });
});

describe('Project model', () => {
  test('should have seeded projects', async () => {
    const projects = await Project.findAll();
    expect(projects.length).toBe(2);
  });

  test('should have correct default status', async () => {
    const project = await Project.findOne({ where: { name: 'Project Alpha' } });
    expect(project.status).toBe('active');
  });
});

describe('Ticket model', () => {
  test('should have seeded tickets', async () => {
    const tickets = await Ticket.findAll();
    expect(tickets.length).toBe(5);
  });

  test('should have correct default status', async () => {
    const ticket = await Ticket.findOne({ where: { title: 'Fix navigation bug' } });
    expect(ticket.status).toBe('open');
    expect(ticket.priority).toBe('medium');
  });

  test('should belong to a project', async () => {
    const ticket = await Ticket.findOne({
      where: { title: 'Implement login page' },
      include: [{ model: Project, as: 'project' }]
    });
    expect(ticket.project).not.toBeNull();
    expect(ticket.project.name).toBe('Project Alpha');
  });

  test('should have assignee association', async () => {
    const ticket = await Ticket.findOne({
      where: { title: 'Implement login page' },
      include: [{ model: User, as: 'assignee' }]
    });
    expect(ticket.assignee).not.toBeNull();
    expect(ticket.assignee.displayName).toBe('Tanaka Taro');
  });
});

describe('Seed data idempotency', () => {
  test('running seed again should not duplicate data', async () => {
    await seedData();
    const users = await User.findAll();
    expect(users.length).toBe(3);
  });
});
