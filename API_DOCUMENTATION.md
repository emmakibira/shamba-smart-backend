# API Documentation - Shamba Smart Backend

## Base URL

```
http://localhost:8000/api
```

## Authentication

All endpoints (except auth) require authentication. Include the user ID in the request.

## Error Responses

```json
{
  "success": false,
  "errors": {
    "field_name": ["Error message"]
  }
}
```

---

## Authentication Endpoints

### Register User

**POST** `/auth/register/`

Request:

```json
{
  "username": "farmer_john",
  "email": "john@example.com",
  "password": "secure_password",
  "password_confirm": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response:

```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "farmer_john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Login

**POST** `/auth/login/`

Request:

```json
{
  "username": "farmer_john",
  "password": "secure_password"
}
```

Response:

```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "farmer_john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "token": "1"
}
```

### Logout

**POST** `/auth/logout/`

Response:

```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

## Dashboard Endpoints

### Get Dashboard Overview

**GET** `/dashboard/overview/`

Response:

```json
{
  "user": {
    "id": 1,
    "username": "farmer_john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "weather": {
    "temperature": 28,
    "humidity": 65,
    "wind_speed": 12,
    "rainfall": 15.0,
    "condition": "Partly Cloudy",
    "condition_display": "Partly Cloudy",
    "last_updated": "2024-05-14T10:30:00Z"
  },
  "crops": [
    {
      "id": 1,
      "name": "Tomatoes",
      "crop_type": "Vegetable",
      "area_planted": 2.5,
      "health_percentage": 85,
      "planting_date": "2024-03-15",
      "expected_harvest_date": "2024-06-15",
      "status": "growing",
      "image": null,
      "notes": ""
    }
  ],
  "recommendations": [
    {
      "id": 1,
      "crop_name": "Rice",
      "profit_margin": "+32%",
      "season": "Kharif",
      "description": "Best crop for current season",
      "confidence_score": 0.95,
      "icon": "sprout",
      "color": "#2E7D32",
      "bgColor": "#C8E6C9"
    }
  ],
  "unread_alerts": 3
}
```

### Get Current Weather

**GET** `/dashboard/weather/current/`

Response:

```json
{
  "temperature": 28,
  "humidity": 65,
  "wind_speed": 12,
  "rainfall": 15.0,
  "condition": "Partly Cloudy",
  "condition_display": "Partly Cloudy",
  "last_updated": "2024-05-14T10:30:00Z"
}
```

### Get Unread Alerts

**GET** `/dashboard/alerts/unread/`

Response:

```json
[
  {
    "id": 1,
    "title": "Heavy Rain Expected",
    "message": "Heavy rain expected in your area tomorrow",
    "alert_type": "weather",
    "is_read": false,
    "created_at": "2024-05-14T10:15:00Z"
  }
]
```

---

## Crops Endpoints

### List User Crops

**GET** `/crops/crops/`

Response:

```json
[
  {
    "id": 1,
    "name": "Tomatoes",
    "crop_type": "Vegetable",
    "area_planted": 2.5,
    "health_percentage": 85,
    "planting_date": "2024-03-15",
    "expected_harvest_date": "2024-06-15",
    "status": "growing",
    "image": null,
    "notes": "Good growth observed"
  }
]
```

### Create Crop

**POST** `/crops/crops/`

Request:

```json
{
  "name": "Tomatoes",
  "crop_type": "Vegetable",
  "area_planted": 2.5,
  "health_percentage": 90,
  "planting_date": "2024-03-15",
  "expected_harvest_date": "2024-06-15",
  "status": "growing",
  "notes": "Good growth"
}
```

### Get Recommendations

**GET** `/crops/recommendations/`

Response:

```json
[
  {
    "id": 1,
    "crop_name": "Rice",
    "profit_margin": "+32%",
    "season": "Kharif",
    "description": "Best yield in current weather",
    "confidence_score": 0.95,
    "icon": "sprout",
    "color": "#2E7D32",
    "bgColor": "#C8E6C9"
  },
  {
    "id": 2,
    "crop_name": "Wheat",
    "profit_margin": "+28%",
    "season": "Rabi",
    "description": "Good alternative",
    "confidence_score": 0.88,
    "icon": "leaf",
    "color": "#8D6E63",
    "bgColor": "#D7CCC8"
  }
]
```

---

## User Profile Endpoints

### Get Profile

**GET** `/users/profile/`

Response:

```json
{
  "id": 1,
  "username": "farmer_john",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "phone_number": "1234567890",
    "location": "Maharashtra, India",
    "farm_size": 10.5,
    "years_of_experience": 15,
    "bio": "Experienced farmer"
  }
}
```

### Update Profile

**PUT** `/users/profile/`

Request:

```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "profile": {
    "phone_number": "9876543210",
    "location": "Karnataka, India",
    "farm_size": 12.0,
    "years_of_experience": 16,
    "bio": "Very experienced farmer"
  }
}
```

---

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

## Rate Limiting

Currently no rate limiting. Will be added in production.

## CORS

The backend is configured to accept requests from:

- `http://localhost:3000`
- `http://localhost:8000`
- `http://localhost:8082`
- `exp://localhost:8082`
