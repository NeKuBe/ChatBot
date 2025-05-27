// /crawlee/main.js
import { PlaywrightCrawler, Dataset } from 'crawlee';
import express from 'express';
import mercadoLibreScraper from './scrapers/mercadoLibre.js';
import amazonScraper from './scrapers/amazon.js';
import aliexpressScraper from './scrapers/aliexpress.js';

const app = express();
app.use(express.json());

app.post('/buscar', async (req, res) => {
  const { componente, modelo } = req.body;
  const query = `${componente} ${modelo}`;
  const results = [];

  const [mlResults, amazonResults, aliexpressResults] = await Promise.all([
    mercadoLibreScraper(query),
    amazonScraper(query),
    aliexpressScraper(query),
  ]);

  results.push(...mlResults, ...amazonResults, ...aliexpressResults);

  const mejores = results
    .filter(item => item.precio && item.tiempo_entrega)
    .sort((a, b) => (a.precio + a.tiempo_entrega_dias) - (b.precio + b.tiempo_entrega_dias))
    .slice(0, 2);

  res.json(mejores);
});

app.listen(3000, () => {
  console.log('Crawlee API escuchando en puerto 3000');
});
