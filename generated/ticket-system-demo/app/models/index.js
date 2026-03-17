const { Sequelize } = require('sequelize');

// Database connection: use DB_CONNECTION_STRING if provided, otherwise SQLite
const dbConnectionString = process.env.DB_CONNECTION_STRING;

let sequelize;
if (dbConnectionString) {
  sequelize = new Sequelize(dbConnectionString, {
    logging: false
  });
} else {
  const storage = process.env.NODE_ENV === 'test' ? ':memory:' : './database.sqlite';
  sequelize = new Sequelize({
    dialect: 'sqlite',
    storage,
    logging: false
  });
}

// Import models
const User = require('./user')(sequelize);
const Project = require('./project')(sequelize);
const Ticket = require('./ticket')(sequelize);

// Associations
Project.hasMany(Ticket, { foreignKey: 'projectId', as: 'tickets' });
Ticket.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });

User.hasMany(Ticket, { foreignKey: 'assigneeId', as: 'assignedTickets' });
Ticket.belongsTo(User, { foreignKey: 'assigneeId', as: 'assignee' });

User.hasMany(Ticket, { foreignKey: 'creatorId', as: 'createdTickets' });
Ticket.belongsTo(User, { foreignKey: 'creatorId', as: 'creator' });

module.exports = { sequelize, User, Project, Ticket };
