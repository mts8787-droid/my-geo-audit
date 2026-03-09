require('dotenv').config();
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

const geoRoutes = require('./routes/geo');
app.use('/api/geo', geoRoutes);

app.get('/', (req, res) => {
  res.json({ message: 'Geo API is running' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
