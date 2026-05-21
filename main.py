import json
import os
import re
import subprocess
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from rag_retriever import init_manim_rag, retrieve_context

config = dotenv_values(".env")
GEMINI_API_KEY = config.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file.")
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

gemini_model = init_chat_model(
    model="google_genai:gemini-2.5-flash",
    temperature=0,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_manim_rag(k=6)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Stage A: structured scene plan (JSON schema via Pydantic) ---


class PlannedScene(BaseModel):
    """One segment of the animation timeline."""

    scene: int = Field(description="1-based scene index in story order")
    description: str = Field(description="What the viewer sees in this scene")
    animation: str = Field(description="Primary motion / animation for this scene")
    transitions: Optional[str] = Field(
        default=None,
        description="How this scene enters/exits or connects to the next",
    )
    timing: Optional[str] = Field(
        default=None,
        description="Pacing, relative durations, or beats",
    )
    camera: Optional[str] = Field(
        default=None,
        description="Camera framing or movement (e.g. zoom, pan) if needed",
    )
    mathematical_objects: Optional[str] = Field(
        default=None,
        description="Formulas, geometric objects, labels, diagrams to show",
    )


class ScenePlanDocument(BaseModel):
    title: str = Field(description="Short title for the animation")
    scenes: list[PlannedScene] = Field(
        description="Ordered list of scenes; together they cover the full user request"
    )


STAGE_A_SYSTEM = """You are a senior motion-design planner for educational math animations.

The user describes what they want animated. You do NOT write Manim or Python code.

Your job:
- Analyze the request and break the animation into clear scenes in order.
- For each scene: describe visuals, animation, transitions, timing, camera if relevant, and mathematical/visual objects (shapes, equations, labels).
- Keep scenes focused; typical plans have 2–8 scenes unless the user asks for more.

When Manim CE documentation excerpts are included, use them only to align scene ideas with realistic APIs and animation concepts (still no code in your output).

Output must conform exactly to the structured schema you are given (fields only, no code)."""


STAGE_B_SYSTEM = """You are an expert Manim Community Edition (CE) developer.

You always receive a structured scene plan as JSON (title + scenes). Your job is to implement the FULL plan in a single Manim script.

When Manim CE documentation excerpts are included, treat them as the authoritative reference for class names, methods, and animation patterns; prefer APIs and idioms shown there.

Hard requirements:
- Output ONE complete executable Python file.
- Start with: from manim import *
- Define exactly one Scene subclass. Name the class descriptively in PascalCase (e.g. PythagoreanTheoremScene).
- Implement the entire flow inside construct(self), in scene order, matching descriptions, animations, transitions, timing hints, camera notes, and mathematical objects from the plan.
- Use idiomatic Manim CE (Create, FadeIn, Transform, Write, self.play, self.wait, MoveCamera, etc.) as appropriate.
- Do not add markdown, prose, or code fences. Return ONLY raw Python source.

Safety — forbidden in generated code:
exec, eval, compile, __import__, getattr/setattr/delattr with dynamic names from user input,
open, input, breakpoint, subprocess, os.system, socket, pickle.loads, yaml.load (unsafe loaders), or any file/network/shell access.

Prefer simple, readable constructs; avoid metaprogramming and dynamic code generation. DO NOT WRITE ANY COMMENTS JUST WRITE PURE CODE """

def extract_python_code(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _with_rag_block(user_text: str, rag_context: str) -> str:
    if not rag_context.strip():
        return user_text
    return (
        user_text
        + "\n\n---\nRelevant Manim CE documentation (similarity-retrieved):\n"
        + rag_context
    )


def run_stage_a_scene_plan(user_prompt: str, rag_context: str = "") -> ScenePlanDocument:
    planner = gemini_model.with_structured_output(ScenePlanDocument)
    body = _with_rag_block(user_prompt, rag_context)
    messages = [
        SystemMessage(content=STAGE_A_SYSTEM),
        HumanMessage(content=body),
    ]
    plan = planner.invoke(messages)
    if not isinstance(plan, ScenePlanDocument):
        raise TypeError("Structured scene planner returned an unexpected type")
    return plan


def run_stage_b_manim_code(
    plan: ScenePlanDocument,
    user_prompt: str,
    rag_context: str = "",
) -> str:
    plan_json = plan.model_dump_json(indent=2)
    plan_block = (
        "Implement this scene plan as Manim CE Python.\n\n"
        f"```json\n{plan_json}\n```\n\n"
        "Original user request (for context):\n"
        f"{user_prompt}\n\n"
        "Remember: output only raw Python, no fences in your reply."
    )
    body = _with_rag_block(plan_block, rag_context)
    messages = [
        SystemMessage(content=STAGE_B_SYSTEM),
        HumanMessage(content=body),
    ]
    response = gemini_model.invoke(messages)
    text = response.content if isinstance(response.content, str) else str(response.content)
    return extract_python_code(text)


@app.post("/generate")
async def generate(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        print("user prompt:", prompt)

        rag_query_a = prompt
        rag_context_a = retrieve_context(rag_query_a)

        try:
            scene_plan = run_stage_a_scene_plan(prompt, rag_context=rag_context_a)
        except Exception as e:
            print(f"Stage A error: {e}")
            return {"status": "error", "stage": "scene_planning", "message": str(e)}

        plan_dict = scene_plan.model_dump()
        print("scene plan:", json.dumps(plan_dict, indent=2))

        rag_query_b = f"{prompt}\n\nScene plan:\n{scene_plan.model_dump_json(indent=2)}"
        rag_context_b = retrieve_context(rag_query_b)

        try:
            llm_output = run_stage_b_manim_code(
                scene_plan,
                user_prompt=prompt,
                rag_context=rag_context_b,
            )
        except Exception as e:
            print(f"Stage B error: {e}")
            return {
                "status": "error",
                "stage": "code_generation",
                "message": str(e),
                "scene_plan": plan_dict,
            }

        print("llm output (code):", llm_output[:2000], "..." if len(llm_output) > 2000 else "")

        if llm_output.startswith("error:"):
            return {
                "status": "error",
                "stage": "code_generation",
                "message": llm_output,
                "scene_plan": plan_dict,
            }

        scene_match = re.search(r"class\s+(\w+)\s*\(", llm_output)
        if not scene_match:
            return {
                "status": "error",
                "stage": "code_generation",
                "message": "No valid Manim Scene class found",
                "scene_plan": plan_dict,
            }
        scene_name = scene_match.group(1)

        with open("video.py", "w", encoding="utf-8") as f:
            f.write(llm_output)

        result = subprocess.run(
            ["manim", "-qm", "video.py", scene_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "stage": "manim_render",
                "details": result.stderr,
                "scene_plan": plan_dict,
            }

        return {
            "status": "success",
            "scene_name": scene_name,
            "scene_plan": plan_dict,
            "details": result.stderr,
            "stdout": result.stdout,
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}


@app.get("/video")
async def ai_video_retrieve(scene_name: str = "Generated_Scene"):
    try:
        video_path = f"media/videos/video/720p30/{scene_name}.mp4"
        print(video_path)
        if not os.path.exists(video_path):
            return {"status": "error", "message": "video not found."}

        return FileResponse(video_path, media_type="video/mp4")
    except Exception as e:
        return {"status": "error", "message": str(e)}
