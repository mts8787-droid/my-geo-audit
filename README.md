# my-geo

A simple geocoding REST API built with Node.js and Express.

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file and add your API key:
   ```
   PORT=3000
   GEOCODING_API_KEY=your_api_key_here
   ```
4. Start the server:
   ```bash
   node index.js
   ```

## Endpoints

### `GET /`
Returns API status.

### `GET /api/geo/geocode?address=your+address`
Returns geocoding data for the given address.

**Example:**
```
GET /api/geo/geocode?address=New+York
```

### `GET /api/geo/reverse?lat=&lng=`
Returns address data for the given coordinates.

**Example:**
```
GET /api/geo/reverse?lat=40.7128&lng=-74.0060
```
