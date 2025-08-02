# Video Splitter Pro - Windows Setup Guide

## Directory Structure
Create a folder for your project, e.g., `C:\VideoSplitter\`

## Backend Setup

1. **Navigate to backend folder:**
   ```cmd
   cd C:\VideoSplitter\backend
   ```

2. **Create virtual environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Update MongoDB URL if needed: `MONGO_URL=mongodb://localhost:27017`

5. **Start backend:**
   ```cmd
   uvicorn server:app --host 127.0.0.1 --port 8001 --reload
   ```

## Frontend Setup

1. **Navigate to frontend folder:**
   ```cmd
   cd C:\VideoSplitter\frontend
   ```

2. **Install dependencies:**
   ```cmd
   npm install
   ```

3. **Configure environment:**
   - Update `.env` file: `REACT_APP_BACKEND_URL=http://localhost:8001`

4. **Start frontend:**
   ```cmd
   npm start
   ```

## Access the App
- Open browser to: http://localhost:3000
- Backend API: http://localhost:8001/api/

## Troubleshooting
- Ensure MongoDB service is running
- Check Windows Firewall settings
- Verify all prerequisites are installed and in PATH