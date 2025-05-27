import express from 'express';
import { runMercadoLibre } from './mercadolibre_scraper.js';
import { runAmazon } from './amazon_scraper.js';
import { runAliExpress } from './aliexpress_scraper.js';

const app = express();
const PORT = process.env.PORT || 3000;

const postalCode = '80295'; // Código postal fijo

app.get('/search', async (req, res) => {
  const { query, model } = req.query;

  if (!query || !model) {
    return res.status(400).json({ error: 'Faltan parámetros: query y model' });
  }

  try {
    console.log(`🔍 Buscando: ${query} | Modelo: ${model} | CP: ${postalCode}`);

    const [ml, amazon, ali] = await Promise.all([
      runMercadoLibre(query, model, postalCode),
      runAmazon(query, model, postalCode),
      runAliExpress(query, model, postalCode)
    ]);

    return res.json({
      query,
      model,
      postalCode,
      resultados: {
        mercadolibre: ml,
        amazon,
        aliexpress: ali
      }
    });
  } catch (error) {
    console.error('❌ Error en el scraping:', error);
    return res.status(500).json({ error: 'Error al realizar scraping' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 API de Scraper corriendo en http://localhost:${PORT}`);
});