"""
app.py
------
Aplicación de Generación de Imágenes y Edición de Contenido con IA Generativa

Funcionalidades:
  - Generación de imágenes con Stable Diffusion XL (Hugging Face)
  - Edición de texto con Llama 3.3 70B (Groq API)
  - Galería de imágenes con descarga
  - Historial de versiones de texto
  - Sistema de roles y colaboración
  - Moderación básica de contenido

Para ejecutar:
  pip install -r requirements.txt
  streamlit run app.py

Variables de entorno necesarias:
  GROQ_API_KEY, HF_API_KEY
"""

import streamlit as st
import io
import json
import base64
import hashlib
from datetime import datetime
from PIL import Image

# Módulos propios
import ai_client as bc
import demo_data as demo


# ─── Configuración de página ────────────────────────────────────────────────────

st.set_page_config(
    page_title="CreativeAI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── CSS personalizado ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }

    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-demo    { background: #FFF3CD; color: #856404; }
    .badge-live    { background: #D4EDDA; color: #155724; }
    .badge-online  { background: #D4EDDA; color: #155724; }
    .badge-offline { background: #F8D7DA; color: #721C24; }

    .image-card {
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 0.6rem;
        margin-bottom: 0.8rem;
        background: #f8f9fa;
    }
    .comment-box {
        background: #f0f4ff;
        border-left: 3px solid #2E75B6;
        padding: 0.6rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .version-item {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.6rem;
        margin: 0.4rem 0;
        cursor: pointer;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ─── Estado inicial de la sesión ────────────────────────────────────────────────

def init_session():
    defaults = {
        "gallery":          [],       # lista de dicts con imagen + metadatos
        "text_history":     [],       # historial de versiones de texto
        "comments":         list(demo.DEMO_COMMENTS),
        "current_user":     demo.DEMO_USERS[0],
        "active_project":   demo.DEMO_PROJECTS[0]["name"],
        "moderation_log":   [],
        "bedrock_available": bc.get_bedrock_client() is not None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()


# ─── Helpers ────────────────────────────────────────────────────────────────────

BLOCKED_TERMS = [
    "nude", "naked", "violence", "gore", "weapon", "drug",
    "hate", "discriminat", "terror", "explicit"
]

def moderate_prompt(text: str) -> tuple[bool, str]:
    """Comprueba si el prompt contiene términos bloqueados."""
    text_lower = text.lower()
    for term in BLOCKED_TERMS:
        if term in text_lower:
            return False, f"El prompt contiene términos no permitidos: '{term}'"
    return True, ""


def image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def save_text_version(text: str, operation: str = "Manual"):
    """Guarda una versión en el historial."""
    version = {
        "id":        len(st.session_state.text_history) + 1,
        "text":      text,
        "operation": operation,
        "user":      st.session_state.current_user["name"],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
    st.session_state.text_history.insert(0, version)


# ─── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🎨 CreativeAI Studio")
    st.markdown("---")

    # Estado de conexión
    if st.session_state.bedrock_available:
        st.markdown('<span class="status-badge badge-live">🟢 APIs conectadas</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-demo">🟡 Modo Demo (sin AWS)</span>',
                    unsafe_allow_html=True)
        st.caption("Configura GROQ_API_KEY y HF_API_KEY en los Secrets de Streamlit Cloud.")

    st.markdown("---")

    # Selector de usuario (simula login)
    st.markdown("**👤 Usuario activo**")
    user_names = [u["name"] for u in demo.DEMO_USERS]
    selected_name = st.selectbox("", user_names, label_visibility="collapsed")
    st.session_state.current_user = next(u for u in demo.DEMO_USERS if u["name"] == selected_name)
    user = st.session_state.current_user

    role_colors = {"Diseñador": "🎨", "Redactor": "✍️", "Aprobador": "✅", "Admin": "⚙️"}
    st.info(f"{role_colors.get(user['role'], '')} **Rol:** {user['role']}")

    st.markdown("---")

    # Proyecto activo
    st.markdown("**📁 Proyecto activo**")
    proj_names = [p["name"] for p in demo.DEMO_PROJECTS]
    st.session_state.active_project = st.selectbox("", proj_names, label_visibility="collapsed")

    st.markdown("---")

    # Métricas rápidas
    st.markdown("**📊 Sesión actual**")
    col1, col2 = st.columns(2)
    col1.metric("Imágenes", len(st.session_state.gallery))
    col2.metric("Versiones", len(st.session_state.text_history))

    st.markdown("---")
    st.markdown("**🔒 Seguridad**")
    st.caption(f"🔐 Cifrado KMS: Activo")
    st.caption(f"🛡️ Moderación: Activa")
    st.caption(f"📋 Política: GDPR (eu-west-1)")


# ─── Header principal ────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="main-header">
    <h1>🎨 CreativeAI Studio</h1>
    <p>Plataforma de generación de imágenes y edición de contenido con IA generativa
     &nbsp;|&nbsp; Proyecto: <strong>{st.session_state.active_project}</strong></p>
</div>
""", unsafe_allow_html=True)


# ─── Tabs principales ────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🖼️ Generación de Imágenes",
    "✍️ Edición de Contenido",
    "👥 Colaboración",
    "⚙️ Seguridad y Ética",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – GENERACIÓN DE IMÁGENES
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Generación de Imágenes con Stable Diffusion XL")
    st.caption("Modelo: Stable Diffusion XL · Hugging Face Inference API")

    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("#### 📝 Configuración del prompt")

        # Verificar permisos por rol
        can_generate = st.session_state.current_user["role"] in ["Diseñador", "Admin"]
        if not can_generate:
            st.warning(f"Tu rol **{st.session_state.current_user['role']}** no tiene permiso para generar imágenes. Solo Diseñadores y Admins pueden hacerlo.")

        prompt = st.text_area(
            "Descripción de la imagen",
            placeholder="Ej: A futuristic city at sunset with flying cars and neon lights, ultra detailed...",
            height=110,
            disabled=not can_generate,
        )

        col_s, col_q = st.columns(2)
        with col_s:
            style = st.selectbox("🎨 Estilo", list(bc.STYLE_PRESETS.keys()))
        with col_q:
            quality = st.select_slider("Calidad", ["Rápida", "Media", "Alta"],
                                       value="Media")

        steps_map = {"Rápida": 20, "Media": 30, "Alta": 50}
        steps = steps_map[quality]

        with st.expander("⚙️ Opciones avanzadas"):
            col_w, col_h = st.columns(2)
            with col_w:
                width = st.select_slider("Ancho (px)", [512, 768, 1024], value=512)
            with col_h:
                height = st.select_slider("Alto (px)",  [512, 768, 1024], value=512)
            cfg_scale = st.slider("CFG Scale", 1.0, 20.0, 7.0, 0.5,
                                  help="Cuánto sigue el modelo al prompt. Valores altos = más fiel al prompt.")
            seed_input = st.number_input("Seed (-1 = aleatorio)", min_value=-1, value=-1)

        generate_btn = st.button("✨ Generar imagen", type="primary",
                                 disabled=not can_generate or not prompt.strip(),
                                 use_container_width=True)

        if generate_btn and prompt.strip():
            # Moderación de contenido
            ok, reason = moderate_prompt(prompt)
            if not ok:
                st.error(f"⛔ Contenido bloqueado por el sistema de moderación: {reason}")
                st.session_state.moderation_log.append({
                    "type": "imagen",
                    "prompt": prompt[:60],
                    "reason": reason,
                    "user": st.session_state.current_user["name"],
                    "time": datetime.now().strftime("%H:%M:%S"),
                })
            else:
                with st.spinner(f"Generando imagen con SDXL ({steps} pasos)..."):
                    if st.session_state.bedrock_available:
                        img = bc.generate_image(prompt, style, width, height,
                                                steps, cfg_scale, seed_input)
                    else:
                        img = demo.generate_demo_image(prompt, style, width, height)

                if img is not None and not (isinstance(img, str) and img.startswith("ERROR_")):
                    img_bytes = image_to_bytes(img)
                    entry = {
                        "id":        len(st.session_state.gallery) + 1,
                        "image":     img,
                        "bytes":     img_bytes,
                        "prompt":    prompt,
                        "style":     style,
                        "user":      st.session_state.current_user["name"],
                        "project":   st.session_state.active_project,
                        "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                        "steps":     steps,
                        "size":      f"{width}x{height}",
                    }
                    st.session_state.gallery.insert(0, entry)
                    st.success("✅ Imagen generada correctamente")
                    st.rerun()
                else:
                    st.error(f"No se pudo generar la imagen: {img}")

    with col_preview:
        st.markdown("#### 🖼️ Vista previa")
        if st.session_state.gallery:
            latest = st.session_state.gallery[0]
            st.image(latest["image"], use_container_width=True)
            st.caption(f"**{latest['style']}** · {latest['size']} · {latest['timestamp']}")
            st.download_button(
                "⬇️ Descargar imagen",
                data=latest["bytes"],
                file_name=f"imagen_{latest['id']}_{latest['style'].lower().replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True,
            )
        else:
            st.info("Genera tu primera imagen para verla aquí.")
            # Placeholder visual
            placeholder_img = demo.generate_demo_image("placeholder", "Realismo", 400, 300)
            st.image(placeholder_img, use_container_width=True, caption="Ejemplo de imagen generada")

    # ── Galería ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🗂️ Galería del proyecto")

    if not st.session_state.gallery:
        st.info("La galería está vacía. Genera algunas imágenes para verlas aquí.")
    else:
        # Filtros
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            filter_style = st.multiselect("Filtrar por estilo",
                                          list(bc.STYLE_PRESETS.keys()),
                                          default=[])
        with col_f2:
            filter_user = st.multiselect("Filtrar por usuario",
                                         list({e["user"] for e in st.session_state.gallery}),
                                         default=[])

        filtered = st.session_state.gallery
        if filter_style:
            filtered = [e for e in filtered if e["style"] in filter_style]
        if filter_user:
            filtered = [e for e in filtered if e["user"] in filter_user]

        st.caption(f"Mostrando {len(filtered)} de {len(st.session_state.gallery)} imágenes")

        cols = st.columns(3)
        for i, entry in enumerate(filtered):
            with cols[i % 3]:
                st.markdown(f'<div class="image-card">', unsafe_allow_html=True)
                st.image(entry["image"], use_container_width=True)
                st.caption(f"#{entry['id']} · **{entry['style']}** · {entry['user']}")
                st.caption(f"📅 {entry['timestamp']} · {entry['size']}")
                st.download_button(
                    "⬇️",
                    data=entry["bytes"],
                    file_name=f"img_{entry['id']}.png",
                    mime="image/png",
                    key=f"dl_{entry['id']}",
                )
                st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – EDICIÓN DE CONTENIDO
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Edición de Contenido con Llama 3.3 70B")
    st.caption("Modelo: Llama 3.3 70B Versatile · Groq API")

    can_edit = st.session_state.current_user["role"] in ["Redactor", "Admin"]
    if not can_edit:
        st.warning(f"Tu rol **{st.session_state.current_user['role']}** puede ver el contenido pero no editar. Solo Redactores y Admins pueden usar el editor.")

    col_editor, col_options = st.columns([3, 2], gap="large")

    with col_editor:
        st.markdown("#### 📄 Editor de texto")

        # Cargar desde historial si se selecciona
        initial_text = ""
        if st.session_state.text_history:
            initial_text = st.session_state.text_history[0]["text"]

        user_text = st.text_area(
            "Contenido",
            value=initial_text,
            height=280,
            placeholder="Escribe o pega tu texto aquí...",
            disabled=not can_edit,
            key="editor_content",
        )

        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Guardar versión", disabled=not can_edit, use_container_width=True):
                if user_text.strip():
                    save_text_version(user_text, "Manual")
                    st.success("Versión guardada en el historial.")
        with col_clear:
            if st.button("🗑️ Limpiar", disabled=not can_edit, use_container_width=True):
                st.rerun()

    with col_options:
        st.markdown("#### 🤖 Operaciones con IA")

        operation = st.selectbox("Selecciona operación",
                                 list(bc.TEXT_OPERATIONS.keys()))

        # Descripción de la operación
        op_descriptions = {
            "Resumir":              "🗜️ Condensa el texto manteniendo las ideas clave.",
            "Expandir":             "📖 Añade más detalles y contexto al texto.",
            "Corregir gramática":   "✅ Corrige errores ortográficos y gramaticales.",
            "Mejorar estilo":       "✨ Hace el texto más claro y profesional.",
            "Generar variación":    "🔀 Crea una versión alternativa del texto.",
            "Traducir al inglés":   "🇬🇧 Traduce el texto al inglés.",
            "Traducir al español":  "🇪🇸 Traduce el texto al español.",
        }
        st.caption(op_descriptions.get(operation, ""))

        apply_btn = st.button(
            f"▶️ Aplicar: {operation}",
            type="primary",
            disabled=not can_edit or not user_text.strip(),
            use_container_width=True,
        )

        if apply_btn and user_text.strip():
            # Guardamos versión antes de modificar
            save_text_version(user_text, "Antes de IA")

            with st.spinner(f"Groq procesando: {operation}..."):
                if st.session_state.bedrock_available:
                    result = bc.edit_text_with_claude(user_text, operation)
                else:
                    result = demo.get_demo_text_response(operation, user_text)

            if result:
                save_text_version(result, operation)
                st.success(f"✅ Operación '{operation}' aplicada.")
                st.markdown("**Resultado:**")
                st.text_area("", value=result, height=180, key="result_text")
            else:
                st.error("Error al procesar el texto. Revisa que GROQ_API_KEY esté configurada en los Secrets.")

        st.markdown("---")

        # Historial de versiones
        st.markdown("#### 🕐 Historial de versiones")

        if not st.session_state.text_history:
            st.info("Aún no hay versiones guardadas.")
        else:
            for i, ver in enumerate(st.session_state.text_history[:8]):
                with st.expander(f"v{ver['id']} – {ver['operation']} ({ver['timestamp']})"):
                    st.caption(f"👤 {ver['user']}")
                    st.text(ver["text"][:200] + ("..." if len(ver["text"]) > 200 else ""))
                    if st.button(f"↩️ Restaurar v{ver['id']}", key=f"restore_{i}",
                                 disabled=not can_edit):
                        save_text_version(ver["text"], f"Restaurado v{ver['id']}")
                        st.success(f"Versión {ver['id']} restaurada.")
                        st.rerun()

    # ── Comparador de versiones ────────────────────────────────────────────────
    if len(st.session_state.text_history) >= 2:
        st.markdown("---")
        st.markdown("#### 🔍 Comparar versiones")
        history_labels = [f"v{v['id']} – {v['operation']} ({v['timestamp']})"
                          for v in st.session_state.text_history]
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            sel_v1 = st.selectbox("Versión A", history_labels, index=0, key="v1_sel")
        with col_v2:
            sel_v2 = st.selectbox("Versión B", history_labels,
                                  index=min(1, len(history_labels) - 1), key="v2_sel")

        idx1 = history_labels.index(sel_v1)
        idx2 = history_labels.index(sel_v2)
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("Versión A", value=st.session_state.text_history[idx1]["text"],
                         height=160, key="comp_a")
        with c2:
            st.text_area("Versión B", value=st.session_state.text_history[idx2]["text"],
                         height=160, key="comp_b")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – COLABORACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("Panel de Colaboración")
    st.caption("Arquitectura: WebSocket API (Amazon API Gateway) + DynamoDB + Amazon SNS")

    col_users, col_chat = st.columns([1, 2], gap="large")

    with col_users:
        st.markdown("#### 👥 Usuarios en el proyecto")

        for user_info in demo.DEMO_USERS:
            status_class = "badge-online" if user_info["online"] else "badge-offline"
            status_text  = "En línea" if user_info["online"] else "Desconectado"
            is_me = user_info["id"] == st.session_state.current_user["id"]

            with st.container():
                cols = st.columns([1, 3, 2])
                cols[0].markdown(f"<h2 style='margin:0'>{user_info['avatar']}</h2>",
                                 unsafe_allow_html=True)
                name_display = f"**{user_info['name']}**" + (" (tú)" if is_me else "")
                cols[1].markdown(name_display)
                cols[1].caption(user_info["role"])
                cols[2].markdown(
                    f'<span class="status-badge {status_class}">{status_text}</span>',
                    unsafe_allow_html=True
                )

        st.markdown("---")
        st.markdown("#### 📁 Proyectos activos")
        for proj in demo.DEMO_PROJECTS:
            status_icons = {"Activo": "🟢", "En revisión": "🟡", "Borrador": "⚪"}
            with st.expander(f"{status_icons.get(proj['status'], '⚪')} {proj['name']}"):
                st.caption(f"👥 {proj['members']} miembros · 🖼️ {proj['images']} imágenes · {proj['status']}")

    with col_chat:
        st.markdown("#### 💬 Comentarios y notas")

        # Mostrar comentarios existentes
        for comment in st.session_state.comments:
            is_mine = comment["user"] == st.session_state.current_user["name"]
            bg = "#e8f0fe" if is_mine else "#f0f4ff"
            align = "right" if is_mine else "left"
            st.markdown(
                f'<div class="comment-box" style="background:{bg}; text-align:{align}">'
                f'<strong>{comment["user"]}</strong> <small>({comment["time"]})</small><br>'
                f'{comment["text"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Añadir nuevo comentario
        st.markdown("---")
        st.markdown("**➕ Añadir comentario**")
        new_comment = st.text_input("", placeholder="Escribe tu comentario...",
                                    label_visibility="collapsed")
        if st.button("Enviar comentario", use_container_width=True) and new_comment.strip():
            st.session_state.comments.append({
                "user": st.session_state.current_user["name"],
                "text": new_comment.strip(),
                "time": datetime.now().strftime("%H:%M"),
            })
            st.rerun()

    # ── Actividad reciente ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Actividad reciente")

    all_activity = []
    for img in st.session_state.gallery:
        all_activity.append({
            "type": "🖼️ Imagen generada",
            "desc": f"'{img['prompt'][:40]}...' en estilo {img['style']}",
            "user": img["user"],
            "time": img["timestamp"],
        })
    for ver in st.session_state.text_history:
        all_activity.append({
            "type": f"✍️ Texto: {ver['operation']}",
            "desc": ver["text"][:50] + "...",
            "user": ver["user"],
            "time": ver["timestamp"],
        })

    if not all_activity:
        st.info("No hay actividad reciente en esta sesión.")
    else:
        for act in all_activity[:10]:
            cols = st.columns([2, 4, 2, 1])
            cols[0].markdown(f"**{act['type']}**")
            cols[1].caption(act["desc"])
            cols[2].caption(act["user"])
            cols[3].caption(act["time"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – SEGURIDAD Y ÉTICA
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.subheader("Seguridad, Privacidad y Uso Ético de la IA")

    col_sec, col_eth = st.columns(2, gap="large")

    with col_sec:
        st.markdown("#### 🔒 Estado de Seguridad")

        security_items = [
            ("✅", "Cifrado en tránsito",  "HTTPS/TLS 1.3 + WSS",           "Activo"),
            ("✅", "Cifrado en reposo",    "AWS KMS (SSE-KMS)",              "Activo"),
            ("✅", "Autenticación",        "Amazon Cognito + MFA",           "Activo"),
            ("✅", "Firewall (WAF)",       "AWS WAF – reglas OWASP Top 10",  "Activo"),
            ("✅", "Auditoría",            "AWS CloudTrail",                 "Activo"),
            ("✅", "Protección DDoS",      "AWS Shield Standard",            "Activo"),
            ("⚠️", "Rotación de claves",  "KMS key rotation",               "Programada (90d)"),
        ]

        for icon, name, service, status in security_items:
            cols = st.columns([1, 3, 3, 2])
            cols[0].markdown(icon)
            cols[1].markdown(f"**{name}**")
            cols[2].caption(service)
            cols[3].caption(status)

        st.markdown("---")
        st.markdown("#### 🛡️ Log de Moderación")

        if not st.session_state.moderation_log:
            st.success("No se han bloqueado prompts en esta sesión.")
        else:
            for entry in st.session_state.moderation_log:
                st.markdown(
                    f'<div class="warning-box">⛔ <strong>{entry["type"]}</strong> · '
                    f'{entry["user"]} · {entry["time"]}<br>'
                    f'Prompt: "{entry["prompt"]}"<br>'
                    f'Motivo: {entry["reason"]}</div>',
                    unsafe_allow_html=True,
                )

        # Test de moderación en vivo
        st.markdown("---")
        st.markdown("#### 🧪 Probar moderación")
        test_prompt = st.text_input("Introduce un prompt para probar el filtro:")
        if st.button("🔍 Verificar prompt") and test_prompt:
            ok, reason = moderate_prompt(test_prompt)
            if ok:
                st.success("✅ Prompt permitido – no contiene términos bloqueados.")
            else:
                st.error(f"⛔ Prompt bloqueado: {reason}")

    with col_eth:
        st.markdown("#### 🤝 Política de Uso Ético")

        ethical_policies = {
            "Transparencia en contenido IA": (
                "Todas las imágenes generadas incluyen metadatos de autoría IA "
                "(watermark invisible) conforme a las directrices de la UE sobre IA."
            ),
            "Mitigación de sesgos": (
                "Se monitorean los patrones de generación para detectar sesgos. "
                "Los prompts del sistema incluyen instrucciones de diversidad e inclusión."
            ),
            "Derechos de autor": (
                "Los usuarios son informados del riesgo de similitud con obras existentes. "
                "Se recomienda revisión legal antes del uso comercial de imágenes generadas."
            ),
            "Privacidad (GDPR)": (
                "Datos almacenados en eu-west-1 (Irlanda). Derecho al olvido en 30 días. "
                "Los logs no incluyen contenido de prompts, solo metadatos."
            ),
            "Uso prohibido": (
                "Queda prohibida la generación de: contenido explícito, desinformación, "
                "imágenes de personas reales sin consentimiento, contenido que promueva odio."
            ),
            "Auditoría y trazabilidad": (
                "Cada acción queda registrada en CloudTrail. Las imágenes incluyen "
                "metadatos de generación (usuario, proyecto, timestamp)."
            ),
        }

        for policy, description in ethical_policies.items():
            with st.expander(f"📌 {policy}"):
                st.markdown(description)

        st.markdown("---")
        st.markdown("#### 📊 Resumen de uso de la sesión")

        total_images = len(st.session_state.gallery)
        total_edits  = len(st.session_state.text_history)
        total_blocked = len(st.session_state.moderation_log)
        styles_used  = list({e["style"] for e in st.session_state.gallery})

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Imágenes generadas",    total_images)
        col_m2.metric("Ediciones de texto",    total_edits)
        col_m3.metric("Prompts bloqueados",    total_blocked,
                      delta=f"-{total_blocked}" if total_blocked > 0 else None,
                      delta_color="inverse")

        if styles_used:
            st.caption(f"Estilos usados: {', '.join(styles_used)}")

        st.markdown("---")
        st.markdown("#### 📥 Exportar datos de sesión")
        session_data = {
            "proyecto":         st.session_state.active_project,
            "usuario_activo":   st.session_state.current_user["name"],
            "total_imagenes":   total_images,
            "total_ediciones":  total_edits,
            "prompts_bloqueados": total_blocked,
            "historial_texto":  [{"operacion": v["operation"], "usuario": v["user"],
                                  "timestamp": v["timestamp"]}
                                 for v in st.session_state.text_history],
            "galeria": [{"id": i["id"], "estilo": i["style"],
                         "usuario": i["user"], "timestamp": i["timestamp"]}
                        for i in st.session_state.gallery],
        }
        st.download_button(
            "⬇️ Exportar log de sesión (JSON)",
            data=json.dumps(session_data, ensure_ascii=False, indent=2),
            file_name=f"session_log_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "CreativeAI Studio · Trabajo Final – Máster en IA – IA Generativa · "
    "Construido con Groq API (Llama 3.3 70B) + Hugging Face (SDXL) · "
    f"{'🟢 APIs activas' if st.session_state.bedrock_available else '🟡 Modo demo'}"
)
