const express = require('express');
const router = express.Router();
const { Project, Ticket, User } = require('../models');

// GET /projects - List all projects
router.get('/', async (req, res) => {
  const projects = await Project.findAll({
    include: [{
      model: Ticket,
      as: 'tickets'
    }],
    order: [['name', 'ASC']]
  });

  res.render('projects/index', { projects });
});

// GET /projects/:id - Show project with tickets
router.get('/:id', async (req, res) => {
  const project = await Project.findByPk(req.params.id, {
    include: [{
      model: Ticket,
      as: 'tickets',
      include: [
        { model: User, as: 'assignee' },
        { model: User, as: 'creator' }
      ]
    }]
  });

  if (!project) {
    return res.status(404).render('error', { message: 'Project not found' });
  }

  res.render('projects/show', { project });
});

module.exports = router;
