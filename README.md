# Shamba Smart Backend

Django REST API backend for the Shamba Smart farming application.

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:8082,exp://localhost:8082
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

## API Endpoints

### Authentication

- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh token

### Dashboard

- `GET /api/dashboard/weather/` - Get weather data
- `GET /api/dashboard/crops/` - Get user's crops
- `GET /api/dashboard/recommendations/` - Get AI recommendations

### Crops

- `GET /api/crops/` - List all crops
- `POST /api/crops/` - Create new crop
- `GET /api/crops/{id}/` - Get crop details
- `PUT /api/crops/{id}/` - Update crop
- `DELETE /api/crops/{id}/` - Delete crop

### User Profile

- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update user profile

## Project Structure

```
shamba-smart-backend/
├── core/                    # Django project settings
├── apps/
│   ├── auth/               # Authentication app
│   ├── dashboard/          # Dashboard data app
│   ├── crops/              # Crops management app
│   └── users/              # User profile app
├── manage.py
└── requirements.txt
```
