const express = require('express');
const router = express.Router();
const Project = require('../models/Project');
const Task = require('../models/Task');
const { requireAuth } = require('../middleware/auth');

router.use(requireAuth);

router.get('/', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const projects = await projectModel.findAll();
    res.render('projects/index', { projects });
  } catch (err) {
    res.render('projects/index', { projects: [] });
  }
});

router.get('/new', (req, res) => {
  res.render('projects/form', { project: null, error: null });
});

router.post('/', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const { name, description } = req.body;
    await projectModel.create({ name, description, owner_id: req.session.userId });
    res.redirect('/projects');
  } catch (err) {
    res.render('projects/form', { project: null, error: 'Failed to create project' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const taskModel = new Task(db);
    const project = await projectModel.findById(req.params.id);
    if (!project) return res.status(404).render('error', { message: 'Project not found' });
    const tasks = await taskModel.findAll({ project_id: req.params.id });
    res.render('projects/show', { project, tasks });
  } catch (err) {
    res.status(500).render('error', { message: 'Failed to load project' });
  }
});

router.get('/:id/edit', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const project = await projectModel.findById(req.params.id);
    if (!project) return res.status(404).render('error', { message: 'Project not found' });
    res.render('projects/form', { project, error: null });
  } catch (err) {
    res.status(500).render('error', { message: 'Failed to load project' });
  }
});

router.post('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    const { name, description, status } = req.body;
    await projectModel.update(req.params.id, { name, description, status });
    res.redirect(`/projects/${req.params.id}`);
  } catch (err) {
    res.redirect(`/projects/${req.params.id}/edit`);
  }
});

router.post('/:id/delete', async (req, res) => {
  try {
    const db = req.app.get('db');
    const projectModel = new Project(db);
    await projectModel.delete(req.params.id);
    res.redirect('/projects');
  } catch (err) {
    res.redirect('/projects');
  }
});

module.exports = router;
