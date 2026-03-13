# 🎨 CreativeAI Studio

Aplicación de generación de imágenes y edición de contenido con IA generativa.
Trabajo Final – Máster en IA – Asignatura: IA Generativa.

## Tecnologías utilizadas

- **Anthropic API** (Claude Haiku) – edición inteligente de texto
- **Hugging Face Inference API** (Stable Diffusion XL) – generación de imágenes
- **Streamlit** – interfaz web desplegada en la nube

## Instrucciones de despliegue

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/creativeai-studio
cd creativeai-studio
```

### 2. Instalar dependencias (local)

```bash
pip install -r requirements.txt
```

### 3. Configurar claves de API

Crea el fichero `.streamlit/secrets.toml` con tus claves:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
HF_API_KEY = "hf_..."
```

> ⚠️ No subas este fichero a GitHub. Está incluido en .gitignore.

### 4. Ejecutar en local

```bash
streamlit run app.py
```

### 5. Desplegar en Streamlit Cloud

1. Sube el código a GitHub (sin el fichero secrets.toml)
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. New app → selecciona el repositorio → fichero: `app.py`
4. En **Advanced settings → Secrets**, pega tu fichero secrets.toml con las claves
5. Click Deploy

## Estructura del proyecto

```
creativeai-studio/
├── app.py              # Aplicación principal (Streamlit)
├── bedrock_client.py   # Integración con Anthropic API y Hugging Face
├── demo_data.py        # Modo demo sin claves API
├── requirements.txt    # Dependencias
└── README.md
```

## Variables de entorno necesarias

| Variable | Dónde conseguirla | Para qué |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | Edición de texto con Claude |
| `HF_API_KEY` | huggingface.co → Settings → Tokens | Generación de imágenes con SDXL |

## Modo demo

Sin claves configuradas, la app funciona en modo demo automáticamente
(imágenes de placeholder, respuestas de texto simuladas).
