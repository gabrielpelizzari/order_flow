# OrderFlow

OrderFlow e um projeto de portfolio para demonstrar processamento assincrono de pedidos usando FastAPI, RabbitMQ, workers e SQLite.

A ideia principal e simples: o usuario cria um pedido, a API salva esse pedido rapidamente, e o processamento acontece em segundo plano por meio de mensagens no RabbitMQ.

```text
Frontend Vue -> FastAPI API -> RabbitMQ -> Workers -> SQLite -> Frontend via polling
```

## Visao geral

O OrderFlow simula o fluxo de uma mini loja:

1. O usuario cria um pedido no frontend.
2. A API recebe o pedido via `POST /orders`.
3. A API valida os dados e salva o pedido como `PENDING`.
4. A API publica o evento `order.created` no RabbitMQ.
5. Os workers consomem os eventos em segundo plano.
6. Cada worker atualiza o status do pedido e publica o proximo evento.
7. O frontend consulta a API periodicamente e mostra o status atual, a timeline e as notificacoes.

O objetivo do projeto e deixar claro como um fluxo assincrono funciona na pratica.

## Arquitetura em alto nivel

```text
Usuario
  |
  v
Frontend Vue
  |
  | POST /orders
  v
FastAPI API
  |
  | salva pedido PENDING
  v
SQLite
  ^
  |
  | atualiza status, eventos e notificacoes
  |
Workers <--- RabbitMQ <--- API publica order.created
```

Fluxo simplificado:

```text
Usuario cria pedido
-> API salva como PENDING
-> API publica order.created
-> RabbitMQ entrega aos workers
-> workers atualizam status
-> frontend consulta API por polling
```

## Stack

- Backend API: Python, FastAPI, uv
- Mensageria: RabbitMQ
- Banco de dados: SQLite
- Frontend: Vue, Axios, Pinia
- Infra local: Docker, Docker Compose

## Pre-requisitos

Para rodar do jeito recomendado:

- Docker Desktop instalado e aberto
- Docker Compose disponivel pelo comando `docker compose`

Para desenvolvimento local sem Docker:

- Python 3.12+
- uv
- Node.js 22+
- npm
- RabbitMQ rodando localmente

## Como rodar com Docker

Na raiz do projeto:

```powershell
docker compose up --build
```

Esse comando sobe:

- RabbitMQ
- API FastAPI
- Frontend Vue
- payment-worker
- stock-worker
- shipping-worker
- notification-worker
- volume SQLite

Para rodar em segundo plano:

```powershell
docker compose up -d --build
```

Para ver os containers:

```powershell
docker compose ps
```

Para ver logs:

```powershell
docker compose logs -f
```

Para parar:

```powershell
docker compose down
```

Para parar e apagar o volume do banco SQLite:

```powershell
docker compose down -v
```

Use `down -v` quando quiser recomecar o projeto com banco limpo.

## URLs do projeto

Com Docker rodando:

```text
Frontend: http://localhost:5173
Tela de criacao: http://localhost:5173/orders/new
API: http://localhost:8000
API docs: http://localhost:8000/docs
RabbitMQ UI: http://localhost:15672
RabbitMQ login: guest / guest
```

Health check da API:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

## Como testar pelo frontend

1. Abra:

```text
http://localhost:5173/orders/new
```

2. Preencha o nome do cliente.
3. Escolha uma opcao em `Simulate event`.
4. Escolha um produto:

```text
Mouse
Keyboard
Monitor
Headset
Webcam
```

5. Ajuste a quantidade.
6. Clique em `Create order`.
7. O frontend vai abrir a tela de detalhe do pedido.
8. Aguarde alguns segundos para os workers processarem.
9. Veja:

- status atual do pedido;
- timeline de eventos;
- notificacoes.

## Cenarios de simulacao

O campo `Simulate event` controla o caminho que o pedido vai seguir.

```text
No simulation
-> PENDING -> PAYMENT_APPROVED -> STOCK_RESERVED -> READY_TO_SHIP
```

```text
Card without limit
-> PENDING -> PAYMENT_REJECTED
```

```text
Invalid card data
-> PENDING -> PAYMENT_REJECTED
```

```text
Payment gateway error
-> PENDING -> PAYMENT_REJECTED
```

```text
Stock unavailable
-> PENDING -> PAYMENT_APPROVED -> STOCK_FAILED
```

Valores tecnicos enviados para a API:

```text
NONE
PAYMENT_CARD_NO_LIMIT
PAYMENT_INVALID_CARD
PAYMENT_GATEWAY_ERROR
STOCK_UNAVAILABLE
```

## Como testar pela API

Criar pedido normal:

```powershell
$body = @{
  customer = @{
    name = "Ana"
    email = "ana@example.com"
  }
  items = @(
    @{
      sku = "SKU-KEYBOARD"
      name = "Keyboard"
      quantity = 1
      unit_price_cents = 19900
    }
  )
  total_cents = 19900
  simulation = "NONE"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/orders `
  -ContentType "application/json" `
  -Body $body
```

Criar pedido com pagamento rejeitado:

```powershell
$body = @{
  customer = @{
    name = "Bruno"
    email = "bruno@example.com"
  }
  items = @(
    @{
      sku = "SKU-MOUSE"
      name = "Mouse"
      quantity = 1
      unit_price_cents = 5900
    }
  )
  total_cents = 5900
  simulation = "PAYMENT_CARD_NO_LIMIT"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/orders `
  -ContentType "application/json" `
  -Body $body
```

Criar pedido com falha de estoque:

```powershell
$body = @{
  customer = @{
    name = "Carla"
    email = "carla@example.com"
  }
  items = @(
    @{
      sku = "SKU-MONITOR"
      name = "Monitor"
      quantity = 1
      unit_price_cents = 89900
    }
  )
  total_cents = 89900
  simulation = "STOCK_UNAVAILABLE"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/orders `
  -ContentType "application/json" `
  -Body $body
```

Listar pedidos:

```powershell
Invoke-RestMethod http://localhost:8000/orders
```

Buscar um pedido especifico:

```powershell
Invoke-RestMethod http://localhost:8000/orders/SEU_ORDER_ID
```

Buscar eventos de um pedido:

```powershell
Invoke-RestMethod http://localhost:8000/orders/SEU_ORDER_ID/events
```

## Fluxo assincrono explicado

### 1. API recebe o pedido

O frontend chama:

```text
POST /orders
```

A API:

- valida cliente, itens, quantidade, preco e total;
- salva o pedido na tabela `orders`;
- salva os itens na tabela `order_items`;
- registra o evento inicial em `order_events`;
- publica `order.created` no RabbitMQ.

O pedido nasce com status:

```text
PENDING
```

### 2. RabbitMQ distribui a mensagem

A API publica o evento na exchange:

```text
orderflow.events
```

O evento inicial tem routing key:

```text
order.created
```

O RabbitMQ entrega essa mensagem para a fila do worker de pagamento:

```text
q.payment.order_created
```

### 3. Payment worker processa pagamento

O `payment-worker` consome `order.created`.

Se a simulacao for:

```text
NONE
STOCK_UNAVAILABLE
```

ele aprova o pagamento:

```text
PENDING -> PAYMENT_APPROVED
```

e publica:

```text
payment.approved
```

Se a simulacao for:

```text
PAYMENT_CARD_NO_LIMIT
PAYMENT_INVALID_CARD
PAYMENT_GATEWAY_ERROR
```

ele rejeita o pagamento:

```text
PENDING -> PAYMENT_REJECTED
```

e publica:

```text
payment.rejected
```

### 4. Stock worker processa estoque

O `stock-worker` consome:

```text
payment.approved
```

Se a simulacao for:

```text
STOCK_UNAVAILABLE
```

ele falha a reserva:

```text
PAYMENT_APPROVED -> STOCK_FAILED
```

e publica:

```text
stock.failed
```

Caso contrario, ele reserva o estoque:

```text
PAYMENT_APPROVED -> STOCK_RESERVED
```

e publica:

```text
stock.reserved
```

### 5. Shipping worker prepara envio

O `shipping-worker` consome:

```text
stock.reserved
```

Depois atualiza:

```text
STOCK_RESERVED -> READY_TO_SHIP
```

e publica:

```text
order.ready_to_ship
```

### 6. Notification worker registra notificacoes

O `notification-worker` escuta eventos importantes:

```text
payment.approved
payment.rejected
stock.failed
order.ready_to_ship
```

Ele salva mensagens na tabela:

```text
notifications
```

Tambem imprime logs no console.

### 7. Frontend acompanha por polling

O frontend nao recebe atualizacao em tempo real por WebSocket nesta versao.

Ele consulta a API periodicamente para atualizar:

- status atual;
- timeline;
- notificacoes.

## RabbitMQ: exchanges, filas e eventos

Exchanges:

| Nome | Tipo | Funcao |
| --- | --- | --- |
| `orderflow.events` | `topic` | Eventos principais do dominio |
| `orderflow.dlx` | `topic` | Dead-letter exchange para falhas |

Filas principais:

| Fila | Routing key |
| --- | --- |
| `q.payment.order_created` | `order.created` |
| `q.stock.payment_approved` | `payment.approved` |
| `q.shipping.stock_reserved` | `stock.reserved` |
| `q.notification.events` | `payment.approved`, `payment.rejected`, `stock.failed`, `order.ready_to_ship` |
| `q.orderflow.dlq` | mensagens mortas |

Filas de retry:

| Fila de retry | Volta para |
| --- | --- |
| `q.payment.order_created.retry` | `order.created` |
| `q.stock.payment_approved.retry` | `payment.approved` |
| `q.shipping.stock_reserved.retry` | `stock.reserved` |
| `q.notification.events.retry` | `notification.retry` |

Regras:

- Mensagem valida e processada: worker da `ack`.
- Payload invalido: mensagem vai para DLQ.
- Erro transitorio: mensagem vai para retry.
- Depois de muitas tentativas: mensagem vai para DLQ.

## Contrato do evento

Exemplo de evento publicado:

```json
{
  "event_id": "uuid",
  "event_type": "order.created",
  "schema_version": 1,
  "occurred_at": "2026-05-05T12:00:00Z",
  "correlation_id": "uuid",
  "producer": "api",
  "data": {
    "order_id": "uuid",
    "customer_name": "Ana",
    "customer_email": "ana@example.com",
    "items": [
      {
        "sku": "SKU-KEYBOARD",
        "name": "Keyboard",
        "quantity": 1,
        "unit_price_cents": 19900
      }
    ],
    "total_cents": 19900,
    "simulation": "NONE"
  },
  "metadata": {
    "retry_count": 0
  }
}
```

Campos importantes:

- `event_id`: identifica o evento.
- `event_type`: tipo do evento.
- `correlation_id`: ajuda a rastrear o fluxo inteiro do pedido.
- `data.order_id`: identifica o pedido.
- `data.simulation`: controla o cenario demonstrado.
- `metadata.retry_count`: controla tentativas.

## Banco de dados SQLite

O SQLite guarda o estado real do sistema.

Tabelas:

| Tabela | Funcao |
| --- | --- |
| `orders` | Pedido e status atual |
| `order_items` | Itens do pedido |
| `order_events` | Timeline de eventos do pedido |
| `notifications` | Mensagens geradas pelos eventos |
| `processed_events` | Evita reprocessar o mesmo evento no mesmo worker |

Status possiveis:

```text
PENDING
PAYMENT_APPROVED
PAYMENT_REJECTED
STOCK_RESERVED
STOCK_FAILED
READY_TO_SHIP
```

Fluxos principais:

```text
PENDING -> PAYMENT_APPROVED -> STOCK_RESERVED -> READY_TO_SHIP
PENDING -> PAYMENT_REJECTED
PAYMENT_APPROVED -> STOCK_FAILED
```

## Workers

### payment-worker

Responsavel por simular o pagamento.

Consome:

```text
order.created
```

Publica:

```text
payment.approved
payment.rejected
```

### stock-worker

Responsavel por simular reserva de estoque.

Consome:

```text
payment.approved
```

Publica:

```text
stock.reserved
stock.failed
```

### shipping-worker

Responsavel por simular preparacao de envio.

Consome:

```text
stock.reserved
```

Publica:

```text
order.ready_to_ship
```

### notification-worker

Responsavel por registrar notificacoes e logs.

Consome:

```text
payment.approved
payment.rejected
stock.failed
order.ready_to_ship
```

## Como rodar testes

Na raiz do projeto:

```powershell
python -m pytest
```

Build do frontend:

```powershell
cd frontend
npm install
npm run build
cd ..
```

Validar Docker Compose:

```powershell
docker compose config
```

## Como rodar localmente sem Docker

Este caminho e mais trabalhoso. Use Docker para a demonstracao principal.

### 1. Subir RabbitMQ

Voce precisa ter um RabbitMQ acessivel em:

```text
amqp://guest:guest@localhost:5672/%2F
```

Uma forma simples e subir apenas o RabbitMQ via Docker:

```powershell
docker compose up -d rabbitmq
```

### 2. Rodar API

Em um terminal:

```powershell
cd backend
uv pip install --system "fastapi>=0.115.0" "pika>=1.3.2" "pydantic-settings>=2.6.0" "uvicorn[standard]>=0.32.0"
uvicorn app.main:app --reload
```

### 3. Rodar workers

Abra terminais separados ou use varias abas.

Na raiz do projeto:

```powershell
$env:PYTHONPATH="C:\Users\Usuario\Documents\order_flow\backend;C:\Users\Usuario\Documents\order_flow\workers"
python -m worker_app.consumers.payment_worker
```

Outro terminal:

```powershell
$env:PYTHONPATH="C:\Users\Usuario\Documents\order_flow\backend;C:\Users\Usuario\Documents\order_flow\workers"
python -m worker_app.consumers.stock_worker
```

Outro terminal:

```powershell
$env:PYTHONPATH="C:\Users\Usuario\Documents\order_flow\backend;C:\Users\Usuario\Documents\order_flow\workers"
python -m worker_app.consumers.shipping_worker
```

Outro terminal:

```powershell
$env:PYTHONPATH="C:\Users\Usuario\Documents\order_flow\backend;C:\Users\Usuario\Documents\order_flow\workers"
python -m worker_app.consumers.notification_worker
```

### 4. Rodar frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Troubleshooting

### Docker nao sobe

Verifique se o Docker Desktop esta aberto.

```powershell
docker compose ps
```

### Porta ocupada

O projeto usa:

```text
5173 frontend
8000 API
5672 RabbitMQ
15672 RabbitMQ UI
```

Se alguma porta estiver ocupada, pare o processo conflitante ou altere a porta no `docker-compose.yml`.

### Quero zerar o banco

```powershell
docker compose down -v
docker compose up --build
```

### Pedido fica parado em PENDING

Verifique se os workers estao rodando:

```powershell
docker compose ps
```

Veja logs:

```powershell
docker compose logs -f payment-worker stock-worker shipping-worker notification-worker
```

### RabbitMQ UI nao abre

Confirme se o container esta saudavel:

```powershell
docker compose ps rabbitmq
```

Acesse:

```text
http://localhost:15672
```

Login:

```text
guest / guest
```

## Trade-offs e melhorias futuras

Este projeto prioriza clareza didatica e demonstracao local.

Trade-offs atuais:

- SQLite e RabbitMQ nao compartilham uma transacao distribuida.
- Se um worker salvar no banco e falhar antes de publicar o proximo evento, o fluxo pode parar.
- As simulacoes de pagamento e estoque sao controladas pelo campo `simulation`, nao por integracoes reais.
- O frontend usa polling, nao WebSocket.

Melhorias futuras:

- Implementar outbox pattern.
- Adicionar WebSocket ou Server-Sent Events.
- Criar dashboard de DLQ.
- Permitir reprocessamento manual de mensagens mortas.
- Criar catalogo real de produtos.
- Implementar estoque real com controle de concorrencia.
- Adicionar Alembic para migracoes.
- Criar testes de integracao com RabbitMQ.
- Adicionar CI para testes, lint e build Docker.
