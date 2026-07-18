# Meesho-style Django E-commerce Store

This project is a Django-based e-commerce storefront with product browsing, cart management, authentication, orders, and payment integration. It is structured for deployment on Railway and uses MongoDB via Djongo.

## Features

- Product catalog and search
- User registration, login, and password reset flow
- Cart and checkout experience
- Order management and email notifications
- Stripe and Razorpay integration hooks
- Admin and dashboard support

## Local development

1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy the environment template:
   `copy .env.example .env`
4. Fill in your local environment values in `.env`.
5. Run migrations:
   `python manage.py migrate`
6. Collect static files:
   `python manage.py collectstatic --noinput`
7. Start the development server:
   `python manage.py runserver`

## Environment variables

Set these values before running the app locally or deploying on Railway:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `MONGODB_URI` or `DB_HOST` / `DB_PORT` / `DB_NAME`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `STRIPE_API_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

## Deployment notes

- This project is configured for Railway with a `Procfile` and `railway.json`.
- Static files are served with WhiteNoise in production.
- A MongoDB database is required. The recommended option is MongoDB Atlas or a Railway MongoDB add-on.

## Notes

- The project currently uses Djongo with Django 3.1.12, which is EOL. This is intentional to remain compatible with the existing Djongo package.
