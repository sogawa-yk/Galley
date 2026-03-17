const request = require('supertest');
const { sequelize } = require('../models');
const { seedData } = require('../models/seed');
const { app } = require('../app');

beforeAll(async () => {
  await sequelize.sync({ force: true });
  await seedData();
});

afterAll(async () => {
  await sequelize.close();
});

// Helper to get an authenticated agent
async function getAuthenticatedAgent() {
  const agent = request.agent(app);
  await agent
    .post('/auth/login')
    .send({ username: 'admin', password: 'admin123' });
  return agent;
}

describe('Health endpoint', () => {
  test('GET /health should return ok', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok' });
  });
});

describe('Auth routes', () => {
  test('GET /auth/login should render login page', async () => {
    const res = await request(app).get('/auth/login');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="login-page"');
  });

  test('POST /auth/login with valid credentials should redirect', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'admin', password: 'admin123' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tickets');
  });

  test('POST /auth/login with invalid credentials should show error', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'admin', password: 'wrongpassword' });
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="login-error"');
  });

  test('POST /auth/login with missing fields should show error', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: '', password: '' });
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="login-error"');
  });

  test('POST /auth/login with non-existent user should show error', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'nonexistent', password: 'test' });
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="login-error"');
  });
});

describe('Protected routes (unauthenticated)', () => {
  test('GET /tickets should redirect to login', async () => {
    const res = await request(app).get('/tickets');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });

  test('GET /projects should redirect to login', async () => {
    const res = await request(app).get('/projects');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });
});

describe('Ticket routes (authenticated)', () => {
  let agent;

  beforeAll(async () => {
    agent = await getAuthenticatedAgent();
  });

  test('GET /tickets should list tickets', async () => {
    const res = await agent.get('/tickets');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="tickets-page"');
    expect(res.text).toContain('data-testid="tickets-table"');
  });

  test('GET /tickets/new should show new ticket form', async () => {
    const res = await agent.get('/tickets/new');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="ticket-form"');
  });

  test('POST /tickets should create a ticket', async () => {
    const res = await agent
      .post('/tickets')
      .send({ title: 'Test ticket', description: 'Test description', projectId: '1', priority: 'high' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tickets');
  });

  test('POST /tickets with missing title should show error', async () => {
    const res = await agent
      .post('/tickets')
      .send({ title: '', projectId: '1' });
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="form-error"');
  });

  test('GET /tickets/1 should show ticket detail', async () => {
    const res = await agent.get('/tickets/1');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="ticket-detail-page"');
  });

  test('GET /tickets/999 should return 404', async () => {
    const res = await agent.get('/tickets/999');
    expect(res.status).toBe(404);
  });

  test('POST /tickets/1/status should update status', async () => {
    const res = await agent
      .post('/tickets/1/status')
      .send({ status: 'closed' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tickets/1');
  });

  test('POST /tickets/1/status with invalid status should return 400', async () => {
    const res = await agent
      .post('/tickets/1/status')
      .send({ status: 'invalid_status' });
    expect(res.status).toBe(400);
  });

  test('POST /tickets/999/status should return 404', async () => {
    const res = await agent
      .post('/tickets/999/status')
      .send({ status: 'open' });
    expect(res.status).toBe(404);
  });

  test('POST /tickets/1/assign should update assignee', async () => {
    const res = await agent
      .post('/tickets/1/assign')
      .send({ assigneeId: '2' });
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tickets/1');
  });

  test('POST /tickets/999/assign should return 404', async () => {
    const res = await agent
      .post('/tickets/999/assign')
      .send({ assigneeId: '1' });
    expect(res.status).toBe(404);
  });
});

describe('Project routes (authenticated)', () => {
  let agent;

  beforeAll(async () => {
    agent = await getAuthenticatedAgent();
  });

  test('GET /projects should list projects', async () => {
    const res = await agent.get('/projects');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="projects-page"');
    expect(res.text).toContain('data-testid="projects-table"');
  });

  test('GET /projects/1 should show project with tickets', async () => {
    const res = await agent.get('/projects/1');
    expect(res.status).toBe(200);
    expect(res.text).toContain('data-testid="project-detail-page"');
    expect(res.text).toContain('data-testid="project-tickets-table"');
  });

  test('GET /projects/999 should return 404', async () => {
    const res = await agent.get('/projects/999');
    expect(res.status).toBe(404);
  });
});

describe('Root redirect', () => {
  test('GET / should redirect to login when unauthenticated', async () => {
    const res = await request(app).get('/');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/auth/login');
  });

  test('GET / should redirect to tickets when authenticated', async () => {
    const agent = await getAuthenticatedAgent();
    const res = await agent.get('/');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe('/tickets');
  });
});
