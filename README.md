# Decaf Compiler Project

This is the Decaf Compiler Project which includes a Python Flask backend and a React frontend.

## Directory Structure
- `src/` - all source code files (backend and frontend)
- `docs/` - project report and grammar
- `test/` - sample programs
- `output/` - sample outputs for each module

## Prerequisites
- Node.js (for frontend)
- Python 3 (for backend)

## Build and Run

### Using Makefile
You can use `make` to run the project.
- `make run` - Starts both backend and frontend in separate command windows.
- `make run-backend` - Starts only the backend.
- `make run-frontend` - Starts only the frontend.

### Using build.bat
If you are on Windows, you can simply run the provided `build.bat` script:
```bash
build.bat
```
This will open two new command prompt windows running the backend and frontend.

## Access
- **Backend**: http://localhost:5000
- **Frontend**: http://localhost:5173
