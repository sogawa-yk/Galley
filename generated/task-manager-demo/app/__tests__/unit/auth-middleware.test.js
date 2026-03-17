const { requireAuth, guestOnly, setLocals } = require('../../middleware/auth');

describe('Auth Middleware', () => {
  let req, res, next;

  beforeEach(() => {
    req = { session: {} };
    res = {
      redirect: jest.fn(),
      locals: {},
    };
    next = jest.fn();
  });

  describe('requireAuth', () => {
    test('should call next if user is authenticated', () => {
      req.session.userId = 1;
      requireAuth(req, res, next);
      expect(next).toHaveBeenCalled();
      expect(res.redirect).not.toHaveBeenCalled();
    });

    test('should redirect to login if not authenticated', () => {
      requireAuth(req, res, next);
      expect(res.redirect).toHaveBeenCalledWith('/auth/login');
      expect(next).not.toHaveBeenCalled();
    });

    test('should redirect if session is null', () => {
      req.session = null;
      requireAuth(req, res, next);
      expect(res.redirect).toHaveBeenCalledWith('/auth/login');
    });
  });

  describe('guestOnly', () => {
    test('should call next if not authenticated', () => {
      guestOnly(req, res, next);
      expect(next).toHaveBeenCalled();
    });

    test('should redirect to dashboard if authenticated', () => {
      req.session.userId = 1;
      guestOnly(req, res, next);
      expect(res.redirect).toHaveBeenCalledWith('/dashboard');
      expect(next).not.toHaveBeenCalled();
    });
  });

  describe('setLocals', () => {
    test('should set currentUser and isAuthenticated when logged in', () => {
      req.session.userId = 1;
      req.session.user = { id: 1, username: 'test', display_name: 'Test' };
      setLocals(req, res, next);
      expect(res.locals.currentUser).toEqual({ id: 1, username: 'test', display_name: 'Test' });
      expect(res.locals.isAuthenticated).toBe(true);
      expect(next).toHaveBeenCalled();
    });

    test('should set null user when not logged in', () => {
      setLocals(req, res, next);
      expect(res.locals.currentUser).toBeNull();
      expect(res.locals.isAuthenticated).toBe(false);
      expect(next).toHaveBeenCalled();
    });
  });
});
