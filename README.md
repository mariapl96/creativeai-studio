# 🎨 CreativeAI Studio

Aplicación web de IA generativa para generación de imágenes y edición de contenido.
Trabajo Final – Máster en IA – Asignatura: IA Generativa.

## Demo en vivo

🔗 La app está desplegada en Streamlit Cloud. Accesible desde cualquier navegador sin instalar nada.

## ¿Qué hace?

| Módulo | Tecnología | Descripción |
|---|---|---|
| Generación de imágenes | Hugging Face – Stable Diffusion 2.1 | Genera imágenes a partir de texto con 8 estilos |
| Edición de texto | Anthropic – Claude Haiku | Resume, expande, corrige, traduce con IA |
| Galería | Estado de sesión | Visualiza y descarga imágenes generadas |
| Historial de versiones | Estado de sesión | Versiones de texto con comparador |
| Colaboración | Streamlit | Usuarios, roles, comentarios |
| Seguridad | AWS (arquitectura prod.) | Moderación, cifrado, log de auditoría |

## Estructura del proyecto

```
creativeai-studio/
├── app.py              # Aplicación principal (Streamlit)
├── ai_client.py        # Integración con Anthropic API y Hugging Face
├── demo_data.py        # Modo demo sin claves API
├── requirements.txt    # Dependencias Python
└── README.md
```

## Instalación local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear fichero de claves
mkdir .streamlit
echo 'ANTHROPIC_API_KEY = "sk-ant-..."' > .streamlit/secrets.toml
echo 'HF_API_KEY = "hf_..."' >> .streamlit/secrets.toml

# 3. Ejecutar
streamlit run app.py
```

## Despliegue en Streamlit Cloud

1. Subir los 4 ficheros a GitHub (sin secrets.toml)
2. Ir a share.streamlit.io → New app → seleccionar repo → app.py
3. En Advanced settings → Secrets, pegar las claves:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
HF_API_KEY = "hf_..."
```
4. Deploy → link público en 2-3 minutos

## Claves de API necesarias

| Variable | Dónde conseguirla | Coste |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | Gratuito (créditos iniciales) |
| `HF_API_KEY` | huggingface.co → Settings → Tokens (Read) | Gratuito |

## Modo demo

Sin claves configuradas, la app funciona en modo demo automáticamente:
imágenes de placeholder generadas con PIL y respuestas de texto simuladas.

## Roles de usuario

| Rol | Generar imágenes | Editar texto | Comentar |
|---|---|---|---|
| Diseñador | ✅ | ❌ | ✅ |
| Redactor | ❌ | ✅ | ✅ |
| Aprobador | ❌ | ❌ | ✅ |
| Admin | ✅ | ✅ | ✅ |
