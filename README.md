# 🎬 Manim Video Generator Backend

An intelligent backend service that automatically generates mathematical animations using AI. This system leverages the power of Google's Gemini 2.0 Flash model to convert natural language descriptions into executable Manim code, creating stunning mathematical visualizations and animations without requiring users to write code manually.

The backend intelligently processes user prompts, generates appropriate Manim Python code, dynamically creates a `video.py` file, and executes it to produce high-quality mathematical animations. Perfect for educators, students, and anyone looking to create engaging mathematical content effortlessly.

## ✨ Features

- **🤖 AI-Powered Code Generation**: Utilizes Gemini 2.0 Flash to convert natural language descriptions into precise Manim code
- **🔄 Dynamic File Management**: Automatically generates and manages `video.py` files for each animation request
- **⚡ Fast Processing**: Optimized execution pipeline for quick video generation
- **🎯 Mathematical Focus**: Specialized in creating mathematical animations, visualizations, and educational content
- **🌐 RESTful API**: Clean and intuitive API endpoints for seamless integration
- **📹 High-Quality Output**: Generates professional-grade mathematical animations
- **🛠️ Auto-Execution**: Handles the complete pipeline from code generation to video rendering
- **🔧 Flexible Configuration**: Customizable settings for different animation requirements

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI (Python)
- **AI Model**: Google Gemini 2.0 Flash
- **Animation Engine**: Manim Community Edition
- **Package Manager**: uv (Ultra-fast Python package installer with pyproject.toml support)
- **Environment Management**: Python dotenv
- **Video Processing**: FFmpeg (via Manim)
- **Development Server**: Uvicorn

## 🚀 Setup & Installation

### Step 1: Install uv Package Manager

First, install `uv`, which is a fast Python package installer and resolver:

**On macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative installation via pip:**
```bash
pip install uv
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/shaswatHota/Manim-VidGen-BackEnd.git
cd Manim-VidGen-BackEnd
```

### Step 3: Install Dependencies

**Option 1: Install from pyproject.toml (Recommended)**

Since the project uses a modern `pyproject.toml` configuration, simply run:

```bash
# Install the project and all dependencies
uv sync
```

This will:
- Create a virtual environment automatically
- Install all dependencies listed in `pyproject.toml`
- Use exact versions from `uv.lock` if available
- Set up the project in development mode

**Option 2: Install from uv.lock (Alternative)**

If you prefer manual virtual environment management:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install exact dependencies from lock file
uv sync
```

**Option 3: Install from requirements.txt (Fallback)**

Only if `pyproject.toml` is not available:

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Step 4: Install System Dependencies

**Install system-level dependencies required by Manim:**

> **Note**: These are system libraries that cannot be installed via `uv` or pip. They are required for Manim's graphics rendering and video processing capabilities.

**On macOS:**
```bash
brew install py3cairo ffmpeg
brew install pango pkg-config
```

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential python3-dev libcairo2-dev libpango1.0-dev ffmpeg
```

**On Windows:**
- Install [Chocolatey](https://chocolatey.org/install)
- Then run:
```powershell
choco install ffmpeg
```

## 🔑 Setting up Gemini 2.0 Flash API

### Step 1: Get Your Gemini API Key

1. **Visit Google AI Studio**: Go to [Google AI Studio](https://ai.google.dev/)

2. **Create or Sign In**: Sign in with your Google account or create a new one

3. **Access API Keys**: Click "Get API key" in Google AI Studio

4. **Create New Project**: 
   - You can either create a new Google Cloud project or use an existing one
   - Choose "Create API key in new project" for simplicity

5. **Generate API Key**: 
   - Navigate to Google AI Studio and click the "Create API Key" button
   - Copy the generated API key immediately (you won't be able to see it again)

### Step 2: Configure Environment Variables

1. **Create `.env` file**: In the root directory of your project, create a `.env` file:

```bash
touch .env  # On Windows: type nul > .env
```

2. **Add your API key**: Open the `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Important**: Replace `your_actual_gemini_api_key_here` with the actual API key you copied from Google AI Studio.

### Step 3: Verify API Access

You can test your API key by making a simple request or running the application to ensure it's working correctly.

## 🏃‍♂️ Running the Project

### Step 1: Set up Environment

Make sure you're in the project directory. If you used `uv sync` in Step 3, the virtual environment is already activated:

```bash
cd Manim-VidGen-BackEnd
# Virtual environment should already be active from uv sync
# If not, activate it manually:
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Start the Server

Start the FastAPI development server using Uvicorn with the following command:

```bash
uvicorn main:app --reload --reload-exclude video.py
```

**Command Breakdown:**
- `uvicorn main:app`: Runs the FastAPI app located in `main.py`
- `--reload`: Enables auto-restart when code changes are detected
- `--reload-exclude video.py`: Excludes `video.py` from reload monitoring (important since this file is dynamically generated)

The server will start on `http://localhost:8000` by default.

### Step 3: Verify Installation

1. **Check API Documentation**: Visit `http://localhost:8000/docs` to see the interactive API documentation
2. **Health Check**: Visit `http://localhost:8000/health` to verify the server is running
3. **Test Animation**: Make a POST request to generate your first animation

## 🔧 Troubleshooting

### Common Issues and Solutions

**1. Import Error: No module named 'manim'**
```bash
# Solution: Install manim using uv
uv pip install manim
```

**2. FFmpeg not found**
```bash
# On macOS:
brew install ffmpeg

# On Ubuntu/Debian:
sudo apt install ffmpeg

# On Windows:
choco install ffmpeg
```

**3. Cairo/Pango related errors**
```bash
# On macOS:
brew install py3cairo pango pkg-config

# On Ubuntu/Debian:
sudo apt install libcairo2-dev libpango1.0-dev
```

**4. Permission denied when running uvicorn**
```bash
# Make sure you have proper permissions:
chmod +x main.py
# Or run with python:
python -m uvicorn main:app --reload --reload-exclude video.py
```

**5. Gemini API key issues**
- Verify your API key is correctly set in the `.env` file
- Ensure there are no extra spaces or quotes around the API key
- Check that your Google Cloud project has the Gemini API enabled
- Verify you haven't exceeded API quotas

**6. Port already in use**
```bash
# Use a different port:
uvicorn main:app --reload --reload-exclude video.py --port 8001
```

**7. Virtual environment issues**
```bash
# Recreate virtual environment:
rm -rf .venv
uv venv
source .venv/bin/activate

# Reinstall dependencies from lock file:
uv sync
# OR from requirements.txt:
uv pip install -r requirements.txt
```

**8. Manim rendering issues**
- Ensure you have sufficient disk space for video generation
- Check that the `media` directory has write permissions
- Verify all system dependencies are installed correctly

**9. Dependency conflicts or version issues**
```bash
# Force reinstall all dependencies from lock file:
uv sync --reinstall

# Or reinstall specific problematic packages:
uv pip install --force-reinstall manim fastapi

# Check for dependency conflicts:
uv pip check
```

## 🎯 Next Steps

To complete your Manim Video Generator setup, you'll need to set up the frontend interface. The frontend provides a user-friendly interface for interacting with this backend service.

**Frontend Repository**: [Manim Video Generator Frontend](https://github.com/shaswatHota/Manim_VidGen_FrontEnd)

Clone and set up the frontend to create a complete video generation experience. The frontend will allow users to input natural language descriptions and receive generated mathematical animations seamlessly.

---

Happy animating! 🎬✨