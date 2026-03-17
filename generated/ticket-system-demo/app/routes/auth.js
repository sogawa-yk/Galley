const express = require('express');
const router = express.Router();
const { User } = require('../models');

// GET /auth/login
router.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/tickets');
  }
  res.render('auth/login', { error: null });
});

// POST /auth/login
router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.render('auth/login', { error: 'Username and password are required' });
  }

  const user = await User.findOne({ where: { username } });
  if (!user) {
    return res.render('auth/login', { error: 'Invalid username or password' });
  }

  const isValid = await user.validatePassword(password);
  if (!isValid) {
    return res.render('auth/login', { error: 'Invalid username or password' });
  }

  req.session.user = {
    id: user.id,
    username: user.username,
    displayName: user.displayName,
    role: user.role
  };

  res.redirect('/tickets');
});

// POST /auth/logout
router.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    res.redirect('/auth/login');
  });
});

module.exports = router;
