const createApp = require('./app');
const { query, closePool } = require('./config/database');

const PORT = parseInt(process.env.PORT || '8080', 10);

async function start() {
  const db = { query };
  const app = createApp(db);

  const server = app.listen(PORT, () => {
    console.log(`Task Manager running on http://localhost:${PORT}`);
  });

  process.on('SIGTERM', async () => {
    console.log('Shutting down...');
    server.close();
    await closePool();
    process.exit(0);
  });
}

start().catch(err => {
  console.error('Failed to start:', err);
  process.exit(1);
});
