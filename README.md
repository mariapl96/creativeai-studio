# 🎨 CreativeAI Studio

Aplicación web de IA generativa para generación de imágenes y edición de contenido.
Trabajo Final – Máster en IA – Asignatura: IA Generativa.

## Tecnologías utilizadas

| Funcionalidad | API | Modelo |
|---|---|---|
| Generación de imágenes | Hugging Face Inference API | Stable Diffusion XL (stabilityai/sdxl-base-1.0) |
| Edición de texto | Groq API | Llama 3.3 70B Versatile |

> 💡 Para los prompts de imágenes usa **inglés** — SD XL está entrenado principalmente en inglés y da mejores resultados. Para edición de texto puedes usar **español** sin problema.

## Estructura del proyecto

```
creativeai-studio/
├── app.py              # Aplicación principal (Streamlit)
├── ai_client.py        # Integración con Groq API y Hugging Face
├── demo_data.py        # Modo demo sin claves API
├── requirements.txt    # Dependencias Python
└── README.md
```

## Instalación local

```bash
pip install -r requirements.txt

# Crear .streamlit/secrets.toml:
GROQ_API_KEY = "gsk_..."
HF_API_KEY = "hf_..."

streamlit run app.py
```

## Despliegue en Streamlit Cloud

1. Subir los ficheros a GitHub (sin secrets.toml)
2. share.streamlit.io → New app → seleccionar repo → app.py
3. Advanced settings → Secrets:
```toml
GROQ_API_KEY = "gsk_..."
HF_API_KEY = "hf_..."
```
4. Deploy → link público en 2-3 minutos

## Claves necesarias

| Variable | Dónde conseguirla | Coste |
|---|---|---|
| `GROQ_API_KEY` | console.groq.com → API Keys | Gratuito |
| `HF_API_KEY` | huggingface.co → Settings → Tokens (Read) | Gratuito |

## Roles de usuario

| Rol | Generar imágenes | Editar texto | Comentar |
|---|---|---|---|
| Diseñador | ✅ | ❌ | ✅ |
| Redactor | ❌ | ✅ | ✅ |
| Aprobador | ❌ | ❌ | ✅ |
| Admin | ✅ | ✅ | ✅ |

## Modo demo

Sin claves configuradas la app funciona en modo demo automáticamente
(imágenes de placeholder con PIL, respuestas de texto simuladas).
