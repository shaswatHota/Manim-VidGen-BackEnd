from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os
from dotenv import dotenv_values
import subprocess
# from groq import Groq
import re
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from google.generativeai.types import GenerationConfig



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
config = dotenv_values(".env")
# client = Groq(api_key=config["GROQ_API_KEY"])
GEMINI_API_KEY = config.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file.")
genai.configure(api_key=GEMINI_API_KEY)


gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

def call_llm(prompt: str) -> str:
    try:
        generation_config = GenerationConfig(
            temperature=0.2,
        )

        response = gemini_model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": "You're a Python tutor that generates only Manim animation code as text with proper indentation dont wrap the code inside this ```python ``` "}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ],
           generation_config=generation_config
        )
        
        generated_text = response.text
        
        
        match = re.search(r"```(?:python)?\n(.*?)```", generated_text, re.DOTALL)
        if match:
            generated_text = match.group(1).strip()
        else:
            generated_text = ""

        return generated_text
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return f"error: {str(e)}"


@app.post("/generate")
async def generate(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        print("llm prompt : ",prompt )
        llm_output = call_llm(prompt)
        print("llm output :", llm_output)
        if "error:" in llm_output:
            return {"status": "error", "message": llm_output}
       
        scene_match = re.search(r"class\s+(\w+)\s*\(", llm_output)
        scene_name = scene_match.group(1) if scene_match else "Generated_Scene"
        
        print(scene_name)

        with open("video.py", "w") as f:
            f.write(llm_output)

        result = subprocess.run(
            ["manim", "-qm", "video.py", scene_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return {"status": "error", "details": result.stderr}

        return {"status": "success","scene_name": scene_name, "details": result.stdout}

    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.get("/video")
async def ai_video_retrieve(scene_name: str="Generated_Scene"):
    try:
        video_path = f"media/videos/video/720p30/{scene_name}.mp4"
        print(video_path)
        if not os.path.exists(video_path) : 
            return {"status":"error","message":"video not found."}
        
        return FileResponse(video_path,media_type="video/mp4")
    except Exception as e:
        return {"status": "error", "message": str(e)}