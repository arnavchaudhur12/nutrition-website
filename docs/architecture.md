# Architecture Overview

## Frontend

- Responsive React storefront with drawer-based mobile-first navigation
- Product cards support variant selection, quantity changes, and dynamic price calculation
- Cart and account actions are modeled as independent panels so the interaction pattern stays close to the provided references

## Backend

- `api/routes`: thin HTTP layer
- `schemas`: request and response contracts
- `repositories`: database access concerns
- `services`: business logic for auth, products, orders, payments, emails, and metrics
- `models`: SQLAlchemy entities
- `core`: config, security, and logging

## Data Model

- `users`: customer and admin accounts
- `products`: sellable catalog entries
- `product_variants`: size and pricing combinations
- `orders`: checkout records and delivery details
- `order_items`: immutable purchased line items
- `feedback`: customer reviews and product ratings
- `newsletter_subscribers`: marketing capture

## Deployment Direction

- Frontend can be built as static assets
- Backend requires a persistent Python runtime, database connectivity, and webhook/email support
- Recommended production topology:
  - GoDaddy domain and DNS management
  - VPS for FastAPI app, reverse proxy, SSL, and background operations
  - PostgreSQL in production

