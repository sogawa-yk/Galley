const express = require('express');
const router = express.Router();
const Task = require('../models/Task');
const Project = require('../models/Project');
const { requireAuth } = require('../middleware/auth');

router.get('/', requireAuth, async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const projectModel = new Project(db);

    const tasks = await taskModel.findAll({ assignee_id: req.session.userId });
    const projects = await projectModel.findAll();
    const statusCounts = await taskModel.getStatusCounts();

    const stats = { todo: 0, in_progress: 0, done: 0 };
    statusCounts.forEach(row => {
      stats[row.status] = row.count;
    });

    res.render('dashboard/index', { tasks, projects, stats });
  } catch (err) {
    res.render('dashboard/index', { tasks: [], projects: [], stats: { todo: 0, in_progress: 0, done: 0 } });
  }
});

module.exports = router;
