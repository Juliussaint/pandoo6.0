# Inventory Management System

A comprehensive inventory management system built with Django, HTMX, and Tailwind CSS.

## Features

- Product Management
- Stock Level Tracking
- Transaction Recording
- Purchase Order Management
- Supplier Management
- Real-time Stock Alerts
- Interactive Dashboard
- Multi-location Support

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd inventory_project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure MySQL Database**

Create a MySQL database:
```sql
CREATE DATABASE inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update `settings.py` with your database credentials.

5. **Initialize Tailwind**
```bash
python manage.py tailwind install
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Run development servers**

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Tailwind:
```bash
python manage.py tailwind start
```

## Usage

1. Access the application at `http://localhost:8000`
2. Log in with your superuser credentials
3. Start by creating:
   - Locations (warehouses/stores)
   - Suppliers
   - Product Categories
   - Products
4. Record transactions and manage stock levels

## Project Structure
```
inventory_project/
├── products/          # Product catalog
├── stock/            # Stock management
├── transactions/     # Transaction tracking
├── purchases/        # Purchase orders
├── suppliers/        # Supplier management
├── core/            # Dashboard and core functionality
└── templates/       # HTML templates
```

## Technologies

- Django 5.0
- MySQL
- Tailwind CSS
- HTMX
- Alpine.js

## License

MIT