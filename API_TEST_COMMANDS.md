# API Testing Commands (cURL)

## Setup
Before running these commands, ensure your backend is running on `http://localhost:8000`

## 1. Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

## 2. Root Endpoint
```bash
curl -X GET http://localhost:8000/
```

## 3. Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "full_name": "Test User",
    "password": "SecurePassword123!",
    "phone_number": "+919876543210"
  }'
```

## 4. Login (Admin)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jai.lagad@lagadsnutrition.in",
    "password": "Xuv1997$"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

Save the `access_token` for subsequent requests.

## 5. Login (Test User)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePassword123!"
  }'
```

## 6. Get Current User (Protected Endpoint)
Replace `YOUR_ACCESS_TOKEN` with the token from login response:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Example with actual token structure:**
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## 7. Reset Password
```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "new_password": "NewSecurePassword123!"
  }'
```

## 8. Fetch Products (Public Endpoint)
```bash
curl -X GET http://localhost:8000/api/products
```

## 9. Fetch Hero Config (Public Endpoint)
```bash
curl -X GET http://localhost:8000/api/hero
```

## 10. Create Order (Protected - Customer)
Replace `YOUR_ACCESS_TOKEN` with your token:

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "items": [
      {
        "product_id": 1,
        "variant_id": 1,
        "quantity": 2
      }
    ],
    "delivery_address": "123 Main St, City, State 12345",
    "coupon_code": ""
  }'
```

## 11. Fetch My Orders (Protected - Customer)
```bash
curl -X GET http://localhost:8000/api/orders \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 12. Get Admin Metrics (Protected - Admin Only)
```bash
curl -X GET http://localhost:8000/api/admin/metrics \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 13. Fetch All Products (Admin)
```bash
curl -X GET http://localhost:8000/api/admin/products \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 14. Create Product (Protected - Admin Only)
```bash
curl -X POST http://localhost:8000/api/admin/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "slug": "test-product",
    "name": "Test Product",
    "flavour": "Vanilla",
    "description": "A test product for API validation",
    "category": "Test",
    "image_url": "https://example.com/image.jpg",
    "variants": [
      {
        "weight_label": "500g",
        "mrp": 500,
        "selling_price": 400,
        "stock_quantity": 100
      }
    ]
  }'
```

## 15. Update Product (Protected - Admin Only)
```bash
curl -X PUT http://localhost:8000/api/admin/products/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "slug": "test-product-updated",
    "name": "Updated Test Product",
    "flavour": "Chocolate",
    "description": "Updated description",
    "category": "Test",
    "image_url": "https://example.com/image-new.jpg",
    "variants": [
      {
        "weight_label": "1kg",
        "mrp": 800,
        "selling_price": 650,
        "stock_quantity": 50
      }
    ]
  }'
```

## 16. Delete Product (Protected - Admin Only)
```bash
curl -X DELETE http://localhost:8000/api/admin/products/1 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 17. Fetch Coupons (Protected - Admin Only)
```bash
curl -X GET http://localhost:8000/api/admin/coupons \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 18. Create Coupon (Protected - Admin Only)
```bash
curl -X POST http://localhost:8000/api/admin/coupons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "code": "SAVE10",
    "discount_percentage": 10
  }'
```

## 19. Delete Coupon (Protected - Admin Only)
```bash
curl -X DELETE http://localhost:8000/api/admin/coupons/SAVE10 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 20. Submit Feedback (Public or Protected)
```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Great product!",
    "rating": 5
  }'
```

## 21. Subscribe to Newsletter (Public)
```bash
curl -X POST http://localhost:8000/api/newsletter \
  -H "Content-Type: application/json" \
  -d '{
    "email": "subscriber@example.com"
  }'
```

## Quick Test Flow

### Step 1: Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","full_name":"Test User","password":"Test12345!"}'
```

### Step 2: Login to Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test12345!"}'
```

### Step 3: Use Token to Get Current User
```bash
# Replace TOKEN_HERE with the access_token from step 2
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN_HERE"
```

### Step 4: Fetch Public Products
```bash
curl -X GET http://localhost:8000/api/products
```

## Debugging Tips

### Check if Backend is Running
```bash
curl -X GET http://localhost:8000/
```

### View Full Response with Headers
```bash
curl -v -X GET http://localhost:8000/api/health
```

### Save Response to File
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test12345!"}' \
  > response.json
```

### Extract Just Status Code
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health
```

### Pretty Print JSON Response
```bash
curl -X GET http://localhost:8000/api/products | json_pp
# or with jq (if installed)
curl -X GET http://localhost:8000/api/products | jq '.'
```

## Common Response Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate email, etc.)
- `500` - Internal Server Error

## Using Environment Variables in cURL

Save token to variable:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test12345!"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Batch Testing Script

Create a file `test_api.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="SecurePass123!"

echo "=== Testing API Endpoints ==="

echo -e "\n1. Health Check"
curl -X GET $API_URL/api/health

echo -e "\n\n2. Register User"
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"Test User\",\"password\":\"$PASSWORD\"}")
echo $REGISTER_RESPONSE
TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo -e "\n\n3. Get Current User"
curl -X GET $API_URL/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n4. Get Products"
curl -X GET $API_URL/api/products

echo -e "\n\n=== Tests Complete ==="
```

Run with:
```bash
chmod +x test_api.sh
./test_api.sh
```
