# HTTP interface

Main operations:

- `GET/POST /api/suppliers`
- `GET/POST /api/products`
- `GET/POST /api/purchase-orders`
- `POST /api/purchase-orders/:id/receive`

Additional read-only endpoints:

- `GET /api/insights` — aggregated product metrics
- `GET /api/health` — dependency/availability probe

These endpoints are demonstration APIs; no public authentication is implemented. See source and tests for payload fields and status codes.
