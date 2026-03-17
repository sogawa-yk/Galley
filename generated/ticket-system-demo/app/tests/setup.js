const { sequelize } = require('../models');
const { seedData } = require('../models/seed');

beforeAll(async () => {
  await sequelize.sync({ force: true });
  await seedData();
});

afterAll(async () => {
  await sequelize.close();
});
