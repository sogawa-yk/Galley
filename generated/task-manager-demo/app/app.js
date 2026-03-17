const express = require('express');
const session = require('express-session');
const path = require('path');
const { setLocals } = require('./middleware/auth');

function createApp(db) {
  const app = express();

  // View engine
  app.set('view engine', 'ejs');
  app.set('views', path.join(__dirname, 'views'));

  // Middleware
  app.use(express.urlencoded({ extended: true }));
  app.use(express.json());
  app.use(express.static(path.join(__dirname, 'public')));
  app.use(session({
    secret: process.env.SESSION_SECRET || 'task-manager-demo-secret',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 },
  }));

  // Make db available to routes
  app.set('db', db);

  // Set template locals
  app.use(setLocals);

  // Routes
  app.use('/', require('./routes/health'));
  app.use('/auth', require('./routes/auth'));
  app.use('/dashboard', require('./routes/dashboard'));
  app.use('/tasks', require('./routes/tasks'));
  app.use('/projects', require('./routes/projects'));

  // Root redirect
  app.get('/', (req, res) => {
    if (req.session && req.session.userId) {
      return res.redirect('/dashboard');
    }
    res.redirect('/auth/login');
  });

  // Error page
  app.use((req, res) => {
    res.status(404).render('error', { message: 'Page not found' });
  });

  return app;
}

module.exports = createApp;
