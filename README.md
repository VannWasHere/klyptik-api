# Klyptik API

A FastAPI application for generating quiz questions using AI and Firebase authentication.

## Features

- AI-powered quiz generation
- User authentication with Firebase
- Username and email login support
- User profile management

## Setup

### Prerequisites

- Python 3.8+
- Firebase project with Authentication enabled
- Firebase Web API Key

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/klyptik-api.git
   cd klyptik-api
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the root directory with the following content:

   ```
   # Firebase Configuration
   FIREBASE_API_KEY=your_firebase_web_api_key_here

   # Model Configuration
   MODEL_PATH=VannWasHere/qwen3-tuned-response

   # Server Configuration
   PORT=8000
   HOST=0.0.0.0
   DEBUG=True
   ```

6. Replace `your_firebase_web_api_key_here` with your actual Firebase Web API Key from the Firebase Console.

7. Create a `creds` folder and place your Firebase Admin SDK credentials file as `klyptik.json`.

### Running the API

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Authentication

- `POST /auth/register`: Register a new user

  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "confirm_password": "securepassword123"
  }
  ```

- `POST /auth/login`: Login with email or username

  ```json
  {
    "email_or_username": "john@example.com", // or "john"
    "password": "securepassword123"
  }
  ```

- `GET /auth/me`: Get current user info (requires authentication)

- `PUT /auth/me`: Update user profile (requires authentication)
  ```json
  {
    "display_name": "John Smith",
    "photo_url": "https://example.com/photo.jpg"
  }
  ```

### Quiz Generation

- `POST /api/ask`: Generate a quiz
  ```json
  {
    "instruction": "Create 5 questions about Python programming"
  }
  ```

## Authentication Flow

1. User registers with name, email, and password
2. A username is automatically generated from the email (or provided by the user)
3. User can login with either email or username
4. Upon successful authentication, a token is provided
5. This token must be included in the `Authorization` header as `Bearer <token>` for protected endpoints

## Environment Variables

| Variable         | Description          | Default                          |
| ---------------- | -------------------- | -------------------------------- |
| FIREBASE_API_KEY | Firebase Web API Key | (required)                       |
| MODEL_PATH       | Path to the AI model | VannWasHere/qwen3-tuned-response |
| PORT             | Server port          | 8000                             |
| HOST             | Server host          | 0.0.0.0                          |
| DEBUG            | Enable debug mode    | True                             |
