# Templates Folder

This folder contains HTML templates for the Parking Detection API.

## Files

### `testing.html`
**Purpose**: Comprehensive API testing dashboard

**Features**:
- ✅ Test all API endpoints from one interface
- ✅ Beautiful, modern UI with tabs
- ✅ Automatic JWT token management
- ✅ Real-time response visualization
- ✅ Request/response timing
- ✅ Color-coded status codes
- ✅ Copy token to clipboard
- ✅ Auto-fill user ID after login

**Endpoints Tested**:

#### Authentication (🔐 Tab)
1. **POST /auth/register** - Register new user account
2. **POST /auth/login** - Login and get JWT token

#### Parking APIs (🅿️ Tab)
3. **POST /parking/updateRaw** - Process raw image with coordinates (JWT required)
4. **POST /parking/update** - Submit edge-processed data (JWT required)
5. **GET /parking/data/<user_id>** - Retrieve parking data (JWT required)

#### Public APIs (🌐 Tab)
6. **GET /health** - Health check endpoint
7. **POST /parking/detect** - Public parking detection (no auth)

## Usage

### Access the Testing Interface

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open in browser**:
   ```
   http://localhost:5001/testing
   ```

### Testing Workflow

1. **Register a User** (Authentication tab)
   - Fill in registration form
   - Click "Register"
   - Note: Username must be unique

2. **Login** (Authentication tab)
   - Enter username and password
   - Click "Login"
   - JWT token will be saved automatically
   - User ID will be auto-filled in other forms

3. **Test Protected Endpoints** (Parking APIs tab)
   - Upload an image for raw processing
   - Submit edge-processed data
   - Retrieve parking data history

4. **Test Public Endpoints** (Public APIs tab)
   - Check API health
   - Test parking detection without authentication

### Tips

- **Token Management**: After login, the JWT token is automatically included in all protected API requests
- **Copy Token**: Click the "Copy" button to copy the JWT token to clipboard
- **Auto-Fill**: User ID is automatically filled after successful login
- **Response Timing**: Each request shows how long it took to complete
- **Status Codes**: Color-coded badges show response status (green=success, red=error)
- **JSON Formatting**: All responses are formatted with syntax highlighting

## Screenshots

### Authentication Tab
Test user registration and login, automatically store JWT tokens.

### Parking APIs Tab
Test all parking-related endpoints with JWT authentication.

### Public APIs Tab
Test publicly accessible endpoints without authentication.

## Technical Details

**Framework**: Vanilla JavaScript (no dependencies)
**Styling**: Custom CSS with gradient backgrounds
**API Base URL**: `http://localhost:5001` (configurable in JS)
**Authentication**: JWT Bearer token in Authorization header

## Customization

To change the API base URL, edit the JavaScript constant:

```javascript
const BASE_URL = 'http://localhost:5001';  // Change this to your API URL
```

## Response Format

Each API call displays:
- **Status Code**: HTTP status with color coding
- **Response Time**: How long the request took (in milliseconds)
- **Response Body**: Full JSON response, formatted and indented

## Error Handling

The interface handles:
- Network errors
- Authentication failures
- Invalid input
- Missing required fields
- Server errors

All errors are displayed in user-friendly format with red backgrounds.

## Future Enhancements

Possible improvements:
- [ ] Save test cases
- [ ] Export responses
- [ ] Request history
- [ ] WebSocket support for real-time updates
- [ ] Dark mode theme
- [ ] Multiple environment support (dev, staging, prod)
- [ ] Request templates/presets
- [ ] Response comparison
- [ ] Performance metrics graph

## Browser Compatibility

Tested on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

Requires modern browser with:
- Fetch API
- ES6+ JavaScript
- CSS Grid support
- FormData API

## Support

For issues or questions:
1. Check the main `ARCHITECTURE.md` documentation
2. Review `API_DOCUMENTATION.md` for endpoint details
3. Check browser console for JavaScript errors
4. Ensure the Flask application is running

---

**Created**: October 2024  
**Version**: 1.0.0
