# Django Boutique - Modern E-commerce Platform

A sophisticated e-commerce solution built with Django, offering seamless payment processing, real-time inventory management, and personalized shopping experiences.

![Django Boutique Demo](docs/images/demo.png)

## Features

- 🛍️ **Product Catalog**
  - Categories and advanced filtering
  - Real-time inventory tracking
  - Related products recommendations

- 👤 **User Management**
  - Custom user profiles
  - Order history tracking
  - Wishlists and favorites

- 🛒 **Shopping Experience**
  - Real-time cart updates with HTMX
  - Multiple payment methods via Stripe
  - Discount and coupon system

- 📱 **Modern Interface**
  - Mobile-responsive design
  - Fast and interactive UI with Alpine.js
  - Real-time search with Elasticsearch

- 📊 **Admin Features**
  - Comprehensive dashboard
  - Sales analytics
  - Inventory management
  - Order processing

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis
- Node.js & npm (for frontend assets)
- AWS Account (for S3 storage)
- Stripe Account

## Installation

1. Clone the repository:
git clone https://github.com/yourusername/django_boutique.git
cd django_boutique

2. Create and activate virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Set up environment variables:
cp .env.example .env
# Edit .env with your configuration

5. Initialize the database:
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata initial_data.json

6. Start development server:
python manage.py runserver

## Usage

### Customer Interface

Visit `http://localhost:8000` to access the store:
- Browse products by category
- Add items to cart
- Process secure payments
- Track orders

### Admin Interface

Visit `http://localhost:8000/admin` to manage:
- Products and inventory
- Orders and customers
- Discounts and promotions
- Analytics dashboard

## API Documentation

RESTful API endpoints are available at `/api/v1/`:

- `GET /api/v1/products/` - List all products
- `GET /api/v1/orders/` - List user orders
- `POST /api/v1/cart/` - Manage shopping cart

Full API documentation available at `/api/docs/`

## Development

### Running Tests
python manage.py test

### Code Quality
flake8
black .

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/django_boutique/issues)
- Email: support@djangoboutique.com

## Acknowledgments

- Django Framework
- Stripe Payment Processing
- TailwindCSS
- HTMX
- Alpine.js

---

Made with ❤️ by [Your Name]

[⬆ back to top](#django-boutique---modern-e-commerce-platform)