function requireAuth(req, res, next) {
  if (req.session && req.session.userId) {
    return next();
  }
  res.redirect('/auth/login');
}

function guestOnly(req, res, next) {
  if (req.session && req.session.userId) {
    return res.redirect('/dashboard');
  }
  next();
}

function setLocals(req, res, next) {
  res.locals.currentUser = req.session ? req.session.user || null : null;
  res.locals.isAuthenticated = !!(req.session && req.session.userId);
  next();
}

module.exports = { requireAuth, guestOnly, setLocals };
