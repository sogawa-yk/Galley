const express = require('express');
const router = express.Router();
const User = require('../models/User');
const { guestOnly } = require('../middleware/auth');

router.get('/login', guestOnly, (req, res) => {
  res.render('auth/login', { error: null });
});

router.post('/login', guestOnly, async (req, res) => {
  try {
    const { username, password } = req.body;
    const userModel = new User(req.app.get('db'));
    const user = await userModel.findByUsername(username);

    if (!user) {
      return res.render('auth/login', { error: 'Invalid username or password' });
    }

    const valid = await userModel.verifyPassword(password, user.password_hash);
    if (!valid) {
      return res.render('auth/login', { error: 'Invalid username or password' });
    }

    req.session.userId = user.id;
    req.session.user = { id: user.id, username: user.username, display_name: user.display_name };
    res.redirect('/dashboard');
  } catch (err) {
    res.render('auth/login', { error: 'Login failed' });
  }
});

router.get('/register', guestOnly, (req, res) => {
  res.render('auth/register', { error: null });
});

router.post('/register', guestOnly, async (req, res) => {
  try {
    const { username, email, password, display_name } = req.body;
    const userModel = new User(req.app.get('db'));

    const existing = await userModel.findByUsername(username);
    if (existing) {
      return res.render('auth/register', { error: 'Username already taken' });
    }

    const userId = await userModel.create({ username, email, password, display_name });
    req.session.userId = userId;
    req.session.user = { id: userId, username, display_name: display_name || username };
    res.redirect('/dashboard');
  } catch (err) {
    res.render('auth/register', { error: 'Registration failed' });
  }
});

router.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/auth/login');
  });
});

module.exports = router;
