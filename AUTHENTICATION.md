# Authentication Module - Keycloak Integration

Complete authentication system using Keycloak Admin API and JWT token validation.

## Features

✅ **Login** - Authenticate with username/password  
✅ **Logout** - Revoke refresh token  
✅ **Refresh Token** - Get new access token  
✅ **Get Current User** - Extract user from JWT  
✅ **Get User by ID** - Admin API to fetch user details  
✅ **List Groups** - Get all Keycloak groups  
✅ **List Group Roles** - Get roles for a group  
✅ **Assign User to Group** - Add user to group  
✅ **Unassign User from Group** - Remove user from group  
✅ **Protected Routes** - All `/api/v1/rules` and `/api/v1/users` endpoints require authentication

## API Endpoints

### Public Endpoints (No Authentication)

#### POST /api/v1/auth/login

Login with username and password.

**Request:**

```json
{
  "username": "john.doe",
  "password": "password123"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

#### POST /api/v1/auth/logout

Logout and revoke refresh token.

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** 204 No Content

#### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

### Protected Endpoints (Require Authentication)

All protected endpoints require the `Authorization` header:

```
Authorization: Bearer <access_token>
```

#### GET /api/v1/auth/me

Get current authenticated user information.

**Response:**

```json
{
  "id": "user-uuid",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "roles": ["user", "admin"]
}
```

#### GET /api/v1/auth/users/{user_id}

Get user by ID (requires `admin` role).

**Response:**

```json
{
  "id": "user-uuid",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "enabled": true,
  "email_verified": true
}
```

#### GET /api/v1/auth/groups

List all groups (requires `admin` role).

**Response:**

```json
[
  {
    "id": "group-uuid",
    "name": "Administrators",
    "path": "/Administrators"
  }
]
```

#### GET /api/v1/auth/groups/{group_id}/roles

List roles for a group (requires `admin` role).

**Response:**

```json
[
  {
    "id": "role-uuid",
    "name": "admin",
    "description": "Administrator role",
    "composite": false
  }
]
```

#### PUT /api/v1/auth/groups/{group_id}/users

Assign user to group (requires `admin` role).

**Request:**

```json
{
  "user_id": "user-uuid"
}
```

**Response:** 204 No Content

#### DELETE /api/v1/auth/groups/{group_id}/users/{user_id}

Remove user from group (requires `admin` role).

**Response:** 204 No Content

## Configuration

### 1. Environment Variables

Set the Keycloak public key:

```bash
export KEYCLOAK_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"
```

### 2. TOML Configuration

**config/local/config.toml:**

```toml
[kc.oauth2]
REALM="eq-prepaid"
CLIENT_ID="eq-prepaid-backend"
AUTHORIZATION_ENDPOINT="/protocol/openid-connect/auth"
TOKEN_ENDPOINT="/protocol/openid-connect/token"
USERINFO_ENDPOINT="/protocol/openid-connect/userinfo"
JWKS_ENDPOINT="/protocol/openid-connect/certs"
LOGOUT_ENDPOINT="/protocol/openid-connect/logout"
SCOPES="openid profile email"
```

**config/local/.secrets.toml:**

```toml
[kc.oauth2]
CLIENT_SECRET = "your-client-secret-here"

[kc_admin]
USER = "admin"
PASSWORD = "admin"
```

## Protected Routes

All routes under `/api/v1/rules` and `/api/v1/users` are automatically protected and require authentication.

### Example: Create Rule (Protected)

```bash
# Login first
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Create rule with token
curl -X POST "http://localhost:8000/api/v1/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Rule",
    "description": "Rule description",
    ...
  }'
```

## Role-Based Access Control

### Using in Controllers

```python
from fastapi import Depends
from modules.auth import AuthUser, get_current_user, require_roles

@router.post("/admin/action")
async def admin_action(
    user: AuthUser = Depends(get_current_user),
    _: None = Depends(require_roles(["admin"]))
):
    # Only users with 'admin' role can access
    return {"message": "Admin action completed"}
```

### Manual Role Checking

```python
from fastapi import Depends
from modules.auth import AuthUser, get_current_user

@router.get("/resource")
async def get_resource(user: AuthUser = Depends(get_current_user)):
    if user.has_role("admin"):
        # Admin access
        return {"data": "full_data"}
    elif user.has_any_role(["viewer", "editor"]):
        # Limited access
        return {"data": "limited_data"}
    else:
        raise HTTPException(403, "Insufficient permissions")
```

## Testing

### 1. Create Keycloak User

1. Go to Keycloak Admin Console: `http://localhost:8080`
2. Select realm: `eq-prepaid`
3. Go to **Users** → **Add user**
4. Set username, email, etc.
5. Go to **Credentials** tab → Set password
6. Go to **Role Mappings** → Assign roles

### 2. Test Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }'
```

### 3. Test Protected Endpoint

```bash
# Get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.access_token')

# Call protected endpoint
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

## Architecture

```
modules/auth/
├── domain/
│   ├── user.py              # AuthUser, KeycloakUser, KeycloakGroup, KeycloakRole
│   └── tokens.py            # TokenResponse, LoginRequest, RefreshTokenRequest
├── infrastructure/
│   └── keycloak/
│       ├── client.py        # KeycloakClient (Admin API)
│       └── jwt_decoder.py   # JWTDecoder (Token validation)
├── application/
│   ├── commands/            # Login, Logout, RefreshToken, AssignUser, UnassignUser
│   ├── queries/             # GetUserById, ListGroups, ListGroupRoles
│   └── dependencies.py      # get_current_user, require_roles, require_all_roles
├── presentation/
│   └── http/
│       ├── controllers/     # Login, Logout, Refresh, Me, Users, Groups
│       └── router.py        # Main auth router
└── auth_provider.py         # Dishka provider
```

## Security Best Practices

1. ✅ **HTTPS in production** - Never send tokens over HTTP
2. ✅ **Short-lived tokens** - Configure in Keycloak (5-15 minutes)
3. ✅ **Refresh tokens** - Use for long-lived sessions
4. ✅ **Token validation** - Verify signature with public key
5. ✅ **Role-based access** - Protect sensitive endpoints
6. ✅ **Audit logging** - Log authentication events
7. ✅ **Rate limiting** - Prevent brute force attacks

## Troubleshooting

### 401 Unauthorized

- Check if token is valid and not expired
- Verify `KEYCLOAK_PUBLIC_KEY` is set correctly
- Ensure `Authorization: Bearer <token>` header is present

### 403 Forbidden

- User is authenticated but lacks required roles
- Check user's role assignments in Keycloak

### Token Expired

- Use refresh token to get new access token
- Call `/api/v1/auth/refresh` endpoint

## Next Steps

- [ ] Implement JWKS fetching from Keycloak
- [ ] Add permission-based access control
- [ ] Add audit logging for auth events
- [ ] Add rate limiting for auth endpoints
- [ ] Implement token blacklist for logout
- [ ] Add multi-tenancy support
