const request = require('supertest');
const createApp = require('../../app');
const { createTestDb } = require('../helpers/testDb');
const User = require('../../models/User');

let db, app;

beforeEach(async () => {
  db = createTestDb();
  app = createApp(db);
});

afterEach(() => {
  db.close();
});

describe('Health Endpoint', () => {
  test('GET /health should return status ok', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok' });
  });
});

describe('Root Redirect', () => {
  test('GET / should redirect to login when not authenticated', async () => {
    const res = await request(app).get('/');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });
});

describe('Auth Routes', () => {
  test('GET /auth/login should render login page', async () => {
    const res = await request(app).get('/auth/login');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="login-page"');
    expect(res.text).toContain('data-testid="login-form"');
  });

  test('GET /auth/register should render register page', async () => {
    const res = await request(app).get('/auth/register');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="register-page"');
    expect(res.text).toContain('data-testid="register-form"');
  });

  test('POST /auth/register should create user and redirect', async () => {
    const res = await request(app)
      .post('/auth/register')
      .type('form')
      .send({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        display_name: 'New User',
      });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/dashboard');
  });

  test('POST /auth/register should reject duplicate username', async () => {
    const userModel = new User(db);
    await userModel.create({
      username: 'existing',
      email: 'existing@example.com',
      password: 'p',
    });

    const res = await request(app)
      .post('/auth/register')
      .type('form')
      .send({
        username: 'existing',
        email: 'new@example.com',
        password: 'password123',
      });
    expect(res.status).toBe(200);
    expect(res.text).toContain('Username already taken');
  });

  test('POST /auth/login should authenticate valid user', async () => {
    // First register
    await request(app)
      .post('/auth/register')
      .type('form')
      .send({
        username: 'logintest',
        email: 'login@example.com',
        password: 'mypassword',
        display_name: 'Login Test',
      });

    // Then login
    const res = await request(app)
      .post('/auth/login')
      .type('form')
      .send({ username: 'logintest', password: 'mypassword' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/dashboard');
  });

  test('POST /auth/login should reject invalid credentials', async () => {
    const res = await request(app)
      .post('/auth/login')
      .type('form')
      .send({ username: 'noone', password: 'wrong' });
    expect(res.status).toBe(200);
    expect(res.text).toContain('Invalid username or password');
  });
});

describe('Protected Routes (unauthenticated)', () => {
  test('GET /dashboard should redirect to login', async () => {
    const res = await request(app).get('/dashboard');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });

  test('GET /tasks should redirect to login', async () => {
    const res = await request(app).get('/tasks');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });

  test('GET /projects should redirect to login', async () => {
    const res = await request(app).get('/projects');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });
});

describe('Authenticated Task Routes', () => {
  let agent;

  beforeEach(async () => {
    agent = request.agent(app);
    // Register and login
    await agent
      .post('/auth/register')
      .type('form')
      .send({
        username: 'taskuser',
        email: 'task@example.com',
        password: 'password123',
        display_name: 'Task User',
      });
  });

  test('GET /tasks should show tasks page', async () => {
    const res = await agent.get('/tasks');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="tasks-page"');
  });

  test('GET /tasks/new should show new task form', async () => {
    const res = await agent.get('/tasks/new');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="task-form"');
  });

  test('POST /tasks should create a task and redirect', async () => {
    const res = await agent
      .post('/tasks')
      .type('form')
      .send({
        title: 'Integration Task',
        description: 'Created in integration test',
        status: 'todo',
        priority: 'high',
      });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tasks');
  });

  test('GET /tasks/:id should show task detail', async () => {
    // Create a task first
    await agent
      .post('/tasks')
      .type('form')
      .send({ title: 'Detail Task', status: 'todo', priority: 'medium' });

    const res = await agent.get('/tasks/1');
    expect(res.status).toBe(200);
    expect(res.text).toContain('Detail Task');
    expect(res.text).toContain('data-testid="task-detail-page"');
  });

  test('GET /tasks/:id for non-existent task should return 404', async () => {
    const res = await agent.get('/tasks/9999');
    expect(res.status).toBe(404);
  });

  test('POST /tasks/:id should update a task', async () => {
    await agent
      .post('/tasks')
      .type('form')
      .send({ title: 'Update Me', status: 'todo', priority: 'low' });

    const res = await agent
      .post('/tasks/1')
      .type('form')
      .send({
        title: 'Updated Task',
        description: 'Updated',
        status: 'done',
        priority: 'high',
      });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tasks/1');
  });

  test('POST /tasks/:id/delete should delete a task', async () => {
    await agent
      .post('/tasks')
      .type('form')
      .send({ title: 'Delete Me', status: 'todo', priority: 'low' });

    const res = await agent.post('/tasks/1/delete');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tasks');
  });
});

describe('Authenticated Project Routes', () => {
  let agent;

  beforeEach(async () => {
    agent = request.agent(app);
    await agent
      .post('/auth/register')
      .type('form')
      .send({
        username: 'projuser',
        email: 'proj@example.com',
        password: 'password123',
        display_name: 'Project User',
      });
  });

  test('GET /projects should show projects page', async () => {
    const res = await agent.get('/projects');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="projects-page"');
  });

  test('POST /projects should create a project', async () => {
    const res = await agent
      .post('/projects')
      .type('form')
      .send({ name: 'Test Project', description: 'A test' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/projects');
  });

  test('GET /projects/:id should show project detail', async () => {
    await agent
      .post('/projects')
      .type('form')
      .send({ name: 'Detail Project', description: 'Details' });

    const res = await agent.get('/projects/1');
    expect(res.status).toBe(200);
    expect(res.text).toContain('Detail Project');
    expect(res.text).toContain('data-testid="project-detail-page"');
  });

  test('POST /projects/:id/delete should delete a project', async () => {
    await agent
      .post('/projects')
      .type('form')
      .send({ name: 'Delete Project' });

    const res = await agent.post('/projects/1/delete');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/projects');
  });
});

describe('Dashboard', () => {
  let agent;

  beforeEach(async () => {
    agent = request.agent(app);
    await agent
      .post('/auth/register')
      .type('form')
      .send({
        username: 'dashuser',
        email: 'dash@example.com',
        password: 'password123',
        display_name: 'Dash User',
      });
  });

  test('GET /dashboard should show dashboard with stats', async () => {
    const res = await agent.get('/dashboard');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="dashboard-page"');
    expect(res.text).toContain('data-testid="dashboard-stats"');
  });
});

describe('404 Page', () => {
  test('GET /nonexistent should return 404', async () => {
    const res = await request(app).get('/nonexistent');
    expect(res.status).toBe(404);
    expect(res.text).toContain('Page not found');
  });
});
