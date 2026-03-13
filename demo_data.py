"""
demo_data.py
------------
Datos y respuestas de ejemplo para el modo demo (sin claves de API).
Simula las respuestas de Groq y Hugging Face para poder presentar la app.
"""

import io
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta


# ─── Imágenes de demostración ───────────────────────────────────────────────────

STYLE_COLORS = {
    "Realismo":         [(70, 130, 180), (100, 160, 210)],
    "Anime":            [(255, 182, 193), (255, 105, 180)],
    "Pintura al óleo":  [(139, 90, 43),  (180, 120, 60)],
    "Boceto digital":   [(50, 50, 80),   (80, 80, 120)],
    "Acuarela":         [(100, 200, 180), (150, 220, 210)],
    "Pixel art":        [(60, 180, 75),  (40, 140, 55)],
    "Cinematográfico":  [(20, 20, 40),   (40, 40, 70)],
    "Fantasía":         [(130, 60, 180), (160, 90, 200)],
}


def generate_demo_image(prompt: str, style: str, width: int = 512, height: int = 512) -> Image.Image:
    """
    Genera una imagen de placeholder para el modo demo.
    Incluye el prompt y estilo como referencia visual.
    """
    colors = STYLE_COLORS.get(style, [(100, 100, 200), (150, 150, 230)])
    bg_color = colors[0]
    accent_color = colors[1]

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Gradiente simulado con rectángulos
    for i in range(0, height, 4):
        alpha = i / height
        r = int(bg_color[0] * (1 - alpha) + accent_color[0] * alpha)
        g = int(bg_color[1] * (1 - alpha) + accent_color[1] * alpha)
        b = int(bg_color[2] * (1 - alpha) + accent_color[2] * alpha)
        draw.rectangle([0, i, width, i + 4], fill=(r, g, b))

    # Formas decorativas
    random.seed(hash(prompt) % 10000)
    for _ in range(8):
        x0 = random.randint(0, width)
        y0 = random.randint(0, height)
        r = random.randint(30, 120)
        opacity_color = tuple(min(255, c + 40) for c in accent_color)
        draw.ellipse([x0 - r, y0 - r, x0 + r, y0 + r],
                     outline=opacity_color, width=2)

    # Texto de demo
    draw.rectangle([20, height - 110, width - 20, height - 20],
                   fill=(0, 0, 0, 180))

    # Etiqueta de estilo
    draw.rectangle([20, 20, 160, 50], fill=accent_color)
    draw.text((30, 28), f"🎨 {style}", fill="white")

    # Prompt truncado
    prompt_short = prompt[:55] + "..." if len(prompt) > 55 else prompt
    draw.text((30, height - 95), "MODO DEMO – Stable Diffusion XL", fill=(255, 200, 100))
    draw.text((30, height - 72), prompt_short, fill=(220, 220, 220))
    draw.text((30, height - 40), "Configura HF_API_KEY para generar imágenes reales", fill=(180, 180, 180))

    return img


# ─── Respuestas de texto de demostración ───────────────────────────────────────

DEMO_RESPONSES = {
    "Resumir": lambda t: f"[DEMO – Llama 3.3] Resumen del texto ({len(t.split())} palabras originales):\n\n{' '.join(t.split()[:30])}{'...' if len(t.split()) > 30 else ''}\n\n→ En modo real, Llama 3.3 70B analizaría el texto completo y generaría un resumen coherente.",
    "Expandir": lambda t: f"[DEMO – Llama 3.3] Versión expandida:\n\n{t}\n\nAdemás, es importante considerar el contexto más amplio de esta idea. Los expertos en el campo han señalado que este tipo de enfoques tiene implicaciones significativas en múltiples áreas. Por ejemplo, desde una perspectiva práctica...\n\n→ En modo real, Llama 3.3 generaría una expansión coherente y contextualizada.",
    "Corregir gramática": lambda t: f"[DEMO – Llama 3.3] Texto corregido:\n\n{t}\n\n→ En modo real, Llama 3.3 detectaría y corregiría errores gramaticales, ortográficos y de puntuación.",
    "Mejorar estilo": lambda t: f"[DEMO – Llama 3.3] Texto con estilo mejorado:\n\n{t}\n\n→ En modo real, Llama 3.3 reformularía el texto para hacerlo más claro, fluido y profesional.",
    "Generar variación": lambda t: f"[DEMO – Llama 3.3] Variación creativa:\n\n{t.replace('es', 'son').replace('un', 'algún')}\n\n→ En modo real, Llama 3.3 generaría una variación manteniendo el significado pero con redacción diferente.",
    "Traducir al inglés": lambda t: f"[DEMO – Llama 3.3] Translation to English:\n\n[This would be an accurate English translation of the Spanish text]\n\nOriginal: {t[:100]}...\n\n→ En modo real, Llama 3.3 traduciría el texto completo al inglés.",
    "Traducir al español": lambda t: f"[DEMO – Llama 3.3] Traducción al español:\n\n[Esta sería una traducción precisa al español]\n\nOriginal: {t[:100]}...\n\n→ En modo real, Llama 3.3 traduciría el texto completo al español.",
}


def get_demo_text_response(operation: str, text: str) -> str:
    fn = DEMO_RESPONSES.get(operation, lambda t: f"[DEMO] Operación '{operation}' aplicada al texto.")
    return fn(text)


# ─── Usuarios y proyectos de demostración ───────────────────────────────────────

DEMO_USERS = [
    {"id": 1, "name": "María García",   "role": "Diseñador",  "avatar": "👩‍🎨", "online": True},
    {"id": 2, "name": "Carlos López",   "role": "Redactor",   "avatar": "✍️",   "online": True},
    {"id": 3, "name": "Ana Martínez",   "role": "Aprobador",  "avatar": "✅",   "online": False},
    {"id": 4, "name": "Luis Fernández", "role": "Admin",      "avatar": "⚙️",   "online": True},
]

DEMO_COMMENTS = [
    {"user": "Carlos López",   "text": "Este prompt funciona muy bien para el estilo cinematográfico.",   "time": "10:32"},
    {"user": "Ana Martínez",   "text": "Aprobado para la campaña de verano ✅",                          "time": "11:15"},
    {"user": "María García",   "text": "He generado 3 variaciones, revisar la galería.",                 "time": "11:48"},
    {"user": "Luis Fernández", "text": "Recordad usar prompts en inglés para mejores resultados.",       "time": "12:01"},
]

DEMO_PROJECTS = [
    {"name": "Campaña Verano 2025",     "members": 3, "images": 12, "status": "Activo"},
    {"name": "Rebranding Corporativo",  "members": 4, "images": 8,  "status": "En revisión"},
    {"name": "Landing Page Producto X", "members": 2, "images": 5,  "status": "Borrador"},
]
