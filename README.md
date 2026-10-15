StyleHub — Smart E-Commerce Platform

A full-stack e-commerce application for browsing fashion products, managing a shopping cart, completing payments, and tracking orders.

Project Overview

StyleHub is built with a React frontend and a FastAPI backend. It provides a fashion-shopping experience with product browsing, cart management, Stripe payment processing, and order history. The application also supports payment-status updates through Stripe webhooks.

Features

Customer Features

* Browse fashion products and product images.
* View products and prices.
* Add products to the shopping cart and manage cart items.
* Proceed to checkout.
* Process test payments using Stripe.
* View order history and order statuses.
* Track successful and failed payment attempts.

Payment Processing

* Stripe PaymentIntent integration.
* Payment confirmation through Stripe webhooks.
* Order status handling, including PENDING, SUCCESS, and FAILED.
* Inventory and cart updates following payment processing.
* Test-mode payment integration for development.

Backend

* FastAPI REST API.
* SQLAlchemy database integration.
* SQLite database for local development.
* Product, cart, and order API modules.
* Authentication and application configuration.

Frontend

* React with Vite.
* Responsive shopping interface.
* Product images and product listings.
* Shopping cart and checkout interface.
* Order history display.

Technology Stack

Component	Technology
Frontend	React, Vite, JavaScript, CSS
Backend	Python, FastAPI
ORM	SQLAlchemy
Database	SQLite
Payments	Stripe
API Testing	FastAPI Swagger UI, Postman

Project Structure

StyleHub/
├── backend/
│   └── app/
│       ├── auth.py
│       ├── cart/
│       ├── orders/
│       │   ├── router.py
│       │   ├── schemas.py
│       │   └── webhook.py
│       ├── products/
│       ├── config.py
│       ├── database.py
│       ├── dependencies.py
│       ├── main.py
│       ├── models.py
│       └── security.py
├── frontend/
│   ├── public/
│   │   └── images/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── CheckoutForm.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md

Prerequisites

Install the following before running the project:

* Python compatible with the project’s installed dependencies.
* Node.js and npm.
* Git.
* A Stripe test-mode account and test API keys.

Backend Setup

Open a terminal in the project root.

1. Activate the virtual environment

On Windows PowerShell:

.\venv\Scripts\Activate.ps1

2. Configure environment variables

Create or configure the root .env file using the variable names expected by backend/app/config.py.

Example:

STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_YOUR_TEST_KEY
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_YOUR_WEBHOOK_SECRET

Use your own Stripe test credentials locally. Never commit real secret values to GitHub.

3. Start the backend

From the project root:

$env:PYTHONPATH = "backend"
uvicorn app.main:app --reload --app-dir backend

Backend base URL:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

Frontend Setup

Open a second terminal:

cd frontend
npm install

Create or configure frontend/.env with the Stripe publishable test key expected by the frontend:

VITE_STRIPE_PUBLISHABLE_KEY=pk_test_REPLACE_WITH_YOUR_PUBLISHABLE_KEY

Start the frontend:

npm run dev

Open the local URL printed by Vite, typically:

http://localhost:5173

Stripe Webhook Setup

For local webhook testing, install and authenticate the Stripe CLI. Keep the CLI listener running in a separate terminal:

stripe listen --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled --forward-to localhost:8000/api/payments/webhook

Copy the webhook signing secret displayed by the CLI into the local root .env as STRIPE_WEBHOOK_SECRET, then restart the backend if required.

Use Stripe test mode only. Never use real card details or expose secret keys.

API Endpoints

The main API areas include:

Area	Purpose
Products	Browse available products
Cart	Manage shopping cart items
Orders	Create orders and retrieve order history
Payments webhook	Receive Stripe payment-status events
Authentication	Handle the application’s authentication flow

The exact request schemas and available operations can be explored in the FastAPI documentation at /docs.

Known order routes include:

* POST /api/orders/ — Create an order and initiate payment.
* GET /api/orders/ — Retrieve order history.
* GET /api/orders/{id} — Retrieve an individual order.
* POST /api/payments/webhook — Process Stripe webhook events.

Testing Checklist

* [ ]	Backend starts without errors.
* [ ]	Frontend starts without errors.
* [ ]	Product listings and images load correctly.
* [ ]	Cart items and totals are correct.
* [ ]	Stripe test checkout works.
* [ ]	Successful payments update the order status to SUCCESS.
* [ ]	Failed payments are represented with the appropriate order status.
* [ ]	Webhook events are processed successfully.
* [ ]	Purchased items are removed from the cart after successful payment.
* [ ]	Order history displays the correct statuses.

Security Notes

* Do not commit .env files or secret keys.
* Do not commit local database files or database backups.
* Use Stripe test-mode credentials during development.
* Never store CVV values.
* Do not use real payment credentials in demonstrations.
* Review .gitignore before uploading the repository.

Future Improvements

* Add automated backend and frontend tests.
* Improve validation and error handling.
* Add deployment configuration.
* Expand reporting and administrative functionality as required.

Author

Developed as a full-stack e-commerce project.