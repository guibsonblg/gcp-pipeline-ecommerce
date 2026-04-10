# Cloud Functions

Cada função fica em sua própria pasta para deployment isolado.

- `bronze_ingest`: processa arquivos JSON colocados no bucket raw e insere nas tabelas Bronze
- `silver_transform`: consome mensagens Pub/Sub e calcula agregações nas tabelas Silver
- `analytics_views`: cria/atualiza views analíticas no dataset Analytics

Todas usam o mesmo conjunto de dependências do GCP.
