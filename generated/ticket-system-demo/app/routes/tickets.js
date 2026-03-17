const express = require('express');
const router = express.Router();
const { Ticket, Project, User } = require('../models');

// GET /tickets - List all tickets
router.get('/', async (req, res) => {
  const tickets = await Ticket.findAll({
    include: [
      { model: Project, as: 'project' },
      { model: User, as: 'assignee' },
      { model: User, as: 'creator' }
    ],
    order: [['createdAt', 'DESC']]
  });

  res.render('tickets/index', { tickets });
});

// GET /tickets/new - New ticket form
router.get('/new', async (req, res) => {
  const projects = await Project.findAll({ where: { status: 'active' } });
  const users = await User.findAll();
  res.render('tickets/new', { projects, users, error: null });
});

// POST /tickets - Create ticket
router.post('/', async (req, res) => {
  const { title, description, priority, projectId, assigneeId } = req.body;

  if (!title || !projectId) {
    const projects = await Project.findAll({ where: { status: 'active' } });
    const users = await User.findAll();
    return res.render('tickets/new', { projects, users, error: 'Title and project are required' });
  }

  await Ticket.create({
    title,
    description: description || null,
    priority: priority || 'medium',
    status: 'open',
    projectId: parseInt(projectId),
    assigneeId: assigneeId ? parseInt(assigneeId) : null,
    creatorId: req.session.user.id
  });

  res.redirect('/tickets');
});

// GET /tickets/:id - Show ticket detail
router.get('/:id', async (req, res) => {
  const ticket = await Ticket.findByPk(req.params.id, {
    include: [
      { model: Project, as: 'project' },
      { model: User, as: 'assignee' },
      { model: User, as: 'creator' }
    ]
  });

  if (!ticket) {
    return res.status(404).render('error', { message: 'Ticket not found' });
  }

  const users = await User.findAll();
  res.render('tickets/show', { ticket, users });
});

// POST /tickets/:id/status - Update ticket status
router.post('/:id/status', async (req, res) => {
  const ticket = await Ticket.findByPk(req.params.id);
  if (!ticket) {
    return res.status(404).json({ error: 'Ticket not found' });
  }

  const { status } = req.body;
  const validStatuses = ['open', 'in_progress', 'resolved', 'closed'];
  if (!validStatuses.includes(status)) {
    return res.status(400).json({ error: 'Invalid status' });
  }

  await ticket.update({ status });
  res.redirect(`/tickets/${ticket.id}`);
});

// POST /tickets/:id/assign - Assign ticket
router.post('/:id/assign', async (req, res) => {
  const ticket = await Ticket.findByPk(req.params.id);
  if (!ticket) {
    return res.status(404).json({ error: 'Ticket not found' });
  }

  const { assigneeId } = req.body;
  await ticket.update({ assigneeId: assigneeId ? parseInt(assigneeId) : null });
  res.redirect(`/tickets/${ticket.id}`);
});

module.exports = router;
