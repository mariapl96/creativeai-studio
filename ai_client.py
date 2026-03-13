"""
ai_client.py
-----------------
Módulo de integración con APIs de IA generativa.

Usa:
  - Anthropic API directa (claude-haiku) para edición de texto
  - Hugging Face Inference API (SDXL) para generación de imágenes

Ambas tienen capa gratuita. Configurar en .streamlit/secrets.toml o
variables de entorno: ANTHROPIC_API_KEY y HF_API_KEY

Si no hay claves configuradas, la app usa modo demo automáticamente.
"""

import os
import io
import requests
from PIL import Image
from groq import Groq


# ─── Claves de API ────────────────────────────────────────────────────────────

def get_groq_key():
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")

def get_hf_key():
    try:
        import streamlit as st
        return st.secrets.get("HF_API_KEY", os.getenv("HF_API_KEY", ""))
    except Exception:
        return os.getenv("HF_API_KEY", "")


# ─── Estilos disponibles ──────────────────────────────────────────────────────

STYLE_PRESETS = {
    "Realismo":         "photorealistic, highly detailed, sharp focus",
    "Anime":            "anime style, vibrant colors, Studio Ghibli",
    "Pintura al óleo":  "oil painting, thick brushstrokes, classical art style",
    "Boceto digital":   "digital sketch, concept art, clean lines",
    "Acuarela":         "watercolor painting, soft colors, artistic",
    "Pixel art":        "pixel art, retro game style, 16-bit",
    "Cinematográfico":  "cinematic shot, dramatic lighting, movie still",
    "Fantasía":         "fantasy art, magical, epic illustration",
}

DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, ugly, bad anatomy, "
    "watermark, text, logo, poorly drawn, nsfw"
)

HF_IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_IMAGE_MODEL}"


# ─── Detección de modo ────────────────────────────────────────────────────────

def get_bedrock_client():
    """Devuelve True si hay alguna API key, None si no (activa modo demo)."""
    if get_groq_key() or get_hf_key():
        return True
    return None


# ─── Generación de imágenes con Hugging Face ──────────────────────────────────

def generate_image(prompt: str, style: str, width: int = 512, height: int = 512,
                   steps: int = 30, cfg_scale: float = 7.0, seed: int = -1):
    """Genera imagen con HF Inference API. Devuelve PIL.Image o None."""
    hf_key = get_hf_key()
    if not hf_key:
        return None

    style_suffix = STYLE_PRESETS.get(style, "")
    full_prompt = f"{prompt}, {style_suffix}" if style_suffix else prompt

    headers = {"Authorization": f"Bearer {hf_key}"}
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
            "width":  min(width, 1024),
            "height": min(height, 1024),
            "guidance_scale": cfg_scale,
            "num_inference_steps": min(steps, 50),
        }
    }
    if seed >= 0:
        payload["parameters"]["seed"] = seed

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        elif response.status_code == 503:
            import time
            time.sleep(20)
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
        return f"ERROR_HF_{response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"ERROR_HF_EXCEPTION: {str(e)}"


# ─── Edición de texto con Anthropic API ──────────────────────────────────────

TEXT_OPERATIONS = {
    "Resumir":                  "resume",
    "Expandir":                 "expand",
    "Corregir gramática":       "correct",
    "Mejorar estilo":           "improve",
    "Generar variación":        "variation",
    "Traducir al inglés":       "translate_en",
    "Traducir al español":      "translate_es",
}

OPERATION_PROMPTS = {
    "resume":       "Resume el siguiente texto de forma concisa, conservando las ideas principales. Responde únicamente con el texto resumido, sin explicaciones adicionales.",
    "expand":       "Expande el siguiente texto añadiendo más detalles, ejemplos y contexto. Responde únicamente con el texto expandido.",
    "correct":      "Corrige todos los errores gramaticales, ortográficos y de puntuación del siguiente texto. Responde únicamente con el texto corregido.",
    "improve":      "Mejora el estilo del siguiente texto haciéndolo más claro, fluido y profesional. Responde únicamente con el texto mejorado.",
    "variation":    "Genera una variación creativa del siguiente texto manteniendo el significado pero cambiando la forma de expresarlo. Responde únicamente con la variación.",
    "translate_en": "Traduce el siguiente texto al inglés de forma natural y fluida. Responde únicamente con la traducción.",
    "translate_es": "Traduce el siguiente texto al español de forma natural y fluida. Responde únicamente con la traducción.",
}


def edit_text_with_claude(text: str, operation: str):
    """Edita texto con Groq API (Llama 3). Devuelve string o None."""
    api_key = get_groq_key()
    if not api_key:
        return None

    op_key = TEXT_OPERATIONS.get(operation, "improve")
    system_prompt = OPERATION_PROMPTS.get(op_key, OPERATION_PROMPTS["improve"])

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"ERROR_GROQ: {str(e)}"
