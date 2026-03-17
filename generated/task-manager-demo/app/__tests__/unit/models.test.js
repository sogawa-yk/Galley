const { createTestDb } = require('../helpers/testDb');
const User = require('../../models/User');
const Project = require('../../models/Project');
const Task = require('../../models/Task');

let db;
let userModel, projectModel, taskModel;

beforeEach(() => {
  db = createTestDb();
  userModel = new User(db);
  projectModel = new Project(db);
  taskModel = new Task(db);
});

afterEach(() => {
  db.close();
});

describe('User Model', () => {
  test('should create a user and return insertId', async () => {
    const id = await userModel.create({
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123',
      display_name: 'Test User',
    });
    expect(id).toBe(1);
  });

  test('should find user by username', async () => {
    await userModel.create({
      username: 'findme',
      email: 'findme@example.com',
      password: 'password123',
      display_name: 'Find Me',
    });
    const user = await userModel.findByUsername('findme');
    expect(user).not.toBeNull();
    expect(user.username).toBe('findme');
    expect(user.display_name).toBe('Find Me');
  });

  test('should find user by id', async () => {
    const id = await userModel.create({
      username: 'byid',
      email: 'byid@example.com',
      password: 'password123',
    });
    const user = await userModel.findById(id);
    expect(user).not.toBeNull();
    expect(user.id).toBe(id);
  });

  test('should return null for non-existent username', async () => {
    const user = await userModel.findByUsername('nonexistent');
    expect(user).toBeNull();
  });

  test('should verify password correctly', async () => {
    await userModel.create({
      username: 'passtest',
      email: 'pass@example.com',
      password: 'secret123',
    });
    const user = await userModel.findByUsername('passtest');
    const valid = await userModel.verifyPassword('secret123', user.password_hash);
    expect(valid).toBe(true);
    const invalid = await userModel.verifyPassword('wrongpass', user.password_hash);
    expect(invalid).toBe(false);
  });

  test('should find all users', async () => {
    await userModel.create({ username: 'u1', email: 'u1@example.com', password: 'p' });
    await userModel.create({ username: 'u2', email: 'u2@example.com', password: 'p' });
    const users = await userModel.findAll();
    expect(users.length).toBe(2);
  });
});

describe('Project Model', () => {
  let ownerId;

  beforeEach(async () => {
    ownerId = await userModel.create({
      username: 'owner',
      email: 'owner@example.com',
      password: 'p',
    });
  });

  test('should create a project', async () => {
    const id = await projectModel.create({
      name: 'Test Project',
      description: 'A test project',
      owner_id: ownerId,
    });
    expect(id).toBeGreaterThan(0);
  });

  test('should find project by id with owner name', async () => {
    const id = await projectModel.create({
      name: 'Find Project',
      description: 'desc',
      owner_id: ownerId,
    });
    const project = await projectModel.findById(id);
    expect(project).not.toBeNull();
    expect(project.name).toBe('Find Project');
    expect(project.owner_name).toBe('owner');
  });

  test('should find all projects', async () => {
    await projectModel.create({ name: 'P1', owner_id: ownerId });
    await projectModel.create({ name: 'P2', owner_id: ownerId });
    const projects = await projectModel.findAll();
    expect(projects.length).toBe(2);
  });

  test('should update a project', async () => {
    const id = await projectModel.create({ name: 'Old Name', owner_id: ownerId });
    await projectModel.update(id, { name: 'New Name', description: 'Updated', status: 'completed' });
    const project = await projectModel.findById(id);
    expect(project.name).toBe('New Name');
    expect(project.status).toBe('completed');
  });

  test('should delete a project', async () => {
    const id = await projectModel.create({ name: 'Delete Me', owner_id: ownerId });
    await projectModel.delete(id);
    const project = await projectModel.findById(id);
    expect(project).toBeNull();
  });
});

describe('Task Model', () => {
  let userId, projectId;

  beforeEach(async () => {
    userId = await userModel.create({
      username: 'taskowner',
      email: 'taskowner@example.com',
      password: 'p',
    });
    projectId = await projectModel.create({
      name: 'Task Project',
      owner_id: userId,
    });
  });

  test('should create a task', async () => {
    const id = await taskModel.create({
      title: 'Test Task',
      description: 'A test task',
      creator_id: userId,
    });
    expect(id).toBeGreaterThan(0);
  });

  test('should create task with all fields', async () => {
    const id = await taskModel.create({
      title: 'Full Task',
      description: 'All fields',
      status: 'in_progress',
      priority: 'high',
      project_id: projectId,
      assignee_id: userId,
      creator_id: userId,
      due_date: '2025-12-31',
    });
    const task = await taskModel.findById(id);
    expect(task.title).toBe('Full Task');
    expect(task.status).toBe('in_progress');
    expect(task.priority).toBe('high');
  });

  test('should find task by id with joined names', async () => {
    const id = await taskModel.create({
      title: 'Joined Task',
      creator_id: userId,
      assignee_id: userId,
      project_id: projectId,
    });
    const task = await taskModel.findById(id);
    expect(task.creator_name).toBe('taskowner');
    expect(task.assignee_name).toBe('taskowner');
    expect(task.project_name).toBe('Task Project');
  });

  test('should find all tasks', async () => {
    await taskModel.create({ title: 'T1', creator_id: userId });
    await taskModel.create({ title: 'T2', creator_id: userId });
    const tasks = await taskModel.findAll();
    expect(tasks.length).toBe(2);
  });

  test('should filter tasks by status', async () => {
    await taskModel.create({ title: 'Todo', status: 'todo', creator_id: userId });
    await taskModel.create({ title: 'Done', status: 'done', creator_id: userId });
    const todoTasks = await taskModel.findAll({ status: 'todo' });
    expect(todoTasks.length).toBe(1);
    expect(todoTasks[0].title).toBe('Todo');
  });

  test('should filter tasks by assignee', async () => {
    const user2 = await userModel.create({ username: 'u2', email: 'u2@x.com', password: 'p' });
    await taskModel.create({ title: 'Assigned', assignee_id: userId, creator_id: userId });
    await taskModel.create({ title: 'Other', assignee_id: user2, creator_id: userId });
    const tasks = await taskModel.findAll({ assignee_id: userId });
    expect(tasks.length).toBe(1);
  });

  test('should update a task', async () => {
    const id = await taskModel.create({ title: 'Old', creator_id: userId });
    await taskModel.update(id, {
      title: 'New',
      description: 'Updated',
      status: 'done',
      priority: 'low',
    });
    const task = await taskModel.findById(id);
    expect(task.title).toBe('New');
    expect(task.status).toBe('done');
  });

  test('should delete a task', async () => {
    const id = await taskModel.create({ title: 'Delete', creator_id: userId });
    await taskModel.delete(id);
    const task = await taskModel.findById(id);
    expect(task).toBeNull();
  });

  test('should get status counts', async () => {
    await taskModel.create({ title: 'T1', status: 'todo', creator_id: userId });
    await taskModel.create({ title: 'T2', status: 'todo', creator_id: userId });
    await taskModel.create({ title: 'T3', status: 'done', creator_id: userId });
    const counts = await taskModel.getStatusCounts();
    expect(counts.length).toBe(2);
    const todoCount = counts.find(c => c.status === 'todo');
    expect(todoCount.count).toBe(2);
  });
});
