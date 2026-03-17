const express = require('express');
const router = express.Router();
const Task = require('../models/Task');
const Project = require('../models/Project');
const User = require('../models/User');
const { requireAuth } = require('../middleware/auth');

router.use(requireAuth);

router.get('/', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const tasks = await taskModel.findAll(req.query);
    res.render('tasks/index', { tasks, filters: req.query });
  } catch (err) {
    res.render('tasks/index', { tasks: [], filters: {} });
  }
});

router.get('/new', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const userModel = new User(db);
    const projects = await projectModel.findAll();
    const users = await userModel.findAll();
    res.render('tasks/form', { task: null, projects, users, error: null });
  } catch (err) {
    res.render('tasks/form', { task: null, projects: [], users: [], error: 'Failed to load form' });
  }
});

router.post('/', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const { title, description, status, priority, project_id, assignee_id, due_date } = req.body;
    await taskModel.create({
      title,
      description,
      status,
      priority,
      project_id: project_id || null,
      assignee_id: assignee_id || null,
      creator_id: req.session.userId,
      due_date: due_date || null,
    });
    res.redirect('/tasks');
  } catch (err) {
    res.redirect('/tasks/new');
  }
});

router.get('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const task = await taskModel.findById(req.params.id);
    if (!task) return res.status(404).render('error', { message: 'Task not found' });
    res.render('tasks/show', { task });
  } catch (err) {
    res.status(500).render('error', { message: 'Failed to load task' });
  }
});

router.get('/:id/edit', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const projectModel = new Project(db);
    const userModel = new User(db);
    const task = await taskModel.findById(req.params.id);
    if (!task) return res.status(404).render('error', { message: 'Task not found' });
    const projects = await projectModel.findAll();
    const users = await userModel.findAll();
    res.render('tasks/form', { task, projects, users, error: null });
  } catch (err) {
    res.status(500).render('error', { message: 'Failed to load task' });
  }
});

router.post('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    const { title, description, status, priority, project_id, assignee_id, due_date } = req.body;
    await taskModel.update(req.params.id, {
      title,
      description,
      status,
      priority,
      project_id: project_id || null,
      assignee_id: assignee_id || null,
      due_date: due_date || null,
    });
    res.redirect(`/tasks/${req.params.id}`);
  } catch (err) {
    res.redirect(`/tasks/${req.params.id}/edit`);
  }
});

router.post('/:id/delete', async (req, res) => {
  try {
    const db = req.app.get('db');
    const taskModel = new Task(db);
    await taskModel.delete(req.params.id);
    res.redirect('/tasks');
  } catch (err) {
    res.redirect('/tasks');
  }
});

module.exports = router;
