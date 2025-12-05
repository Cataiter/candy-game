import streamlit as st
import random
import time
import copy 
import requests 
from streamlit_lottie import st_lottie

# --- CONFIGURACIÓN DE DIFICULTAD ELEVADA ---
ITEMS = ["🔴", "🔵", "🟢", "🟡", "🟣", "🧡"]
ROWS = 8
COLS = 8
BASE_MOVES = 18  # REDUCIDO: Movimientos iniciales en el Nivel 1
BASE_TARGET = 150 
TARGET_MULTIPLIER = 1.75 # AUMENTADO: La meta de puntos se dispara mucho más rápido
# ------------------------------------------

# --- FUNCIONES DE ASISTENCIA Y SOLUCIÓN DEL ERROR LOTTIE ---

@st.cache_data(show_spinner=False)
def load_lottieurl(url: str):
    """Carga una animación Lottie de forma segura, devolviendo None si falla."""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Advertencia: No se pudo cargar Lottie (Estado: {r.status_code})")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Advertencia: Error de conexión al cargar Lottie: {e}")
        return None

# Lottie animation for point gain (Confetti/Stars)
LOTTIE_URL_SUCCESS = "https://assets5.lottiefiles.com/packages/lf20_ebw9x5k.json"
lottie_success = load_lottieurl(LOTTIE_URL_SUCCESS) 

# --- ESTILOS CSS PERSONALIZADOS (SIN CAMBIOS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        /* Regla global de contraste */
        .stApp, .stText, .stMarkdown, p, span, h1, h2, h3, h4 {
            color: #333; 
        }
        
        /* Contenedor principal del juego */
        .stApp {
            background-color: #f0f2f6; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Botones del tablero (Caramelos) */
        .stButton>button {
            font-size: 32px; 
            height: 60px;
            width: 100%;
            border-radius: 12px; 
            border: none;
            box-shadow: 0 4px 0 #999, 0 6px 8px rgba(0,0,0,0.2); 
            transition: all 0.1s ease-out; 
            background-color: white;
            padding: 0;
            line-height: 1;
        }
        
        .stButton>button:hover {
            box-shadow: 0 2px 0 #999, 0 3px 5px rgba(0,0,0,0.2); 
            transform: translateY(2px); 
        }

        /* Botón seleccionado (Animación de resplandor) */
        .selected-btn>button {
            border: 4px solid #ff4b4b !important;
            background-color: #ffecec !important;
            box-shadow: 0 0 15px #ff4b4b, 0 0 5px #ff4b4b; 
            transform: scale(1.05);
            animation: pulse 0.8s infinite alternate; 
        }

        /* Definición de la animación de pulsación */
        @keyframes pulse {
            0% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.5); }
            100% { box-shadow: 0 0 20px rgba(255, 75, 75, 1); }
        }

        /* Título Principal */
        h1 {
            color: #ff4b4b !important; 
            text-align: center;
            letter-spacing: 2px;
            font-weight: 800;
        }
        
        /* Ajuste de métricas */
        [data-testid="stMetricValue"] {
            font-size: 30px;
            font-weight: bold;
            color: #ff4b4b;
        }
        
        /* Fix específico para el texto del Spinner y la barra lateral */
        .stSpinner > div > div > div {
             color: #333 !important;
        }
        .stSidebar label, .stSidebar p {
             color: #333 !important;
        }
        </style>
    """, unsafe_allow_html=True)


# --- LÓGICA DEL JUEGO ---
def init_board():
    board = [[random.choice(ITEMS) for _ in range(COLS)] for _ in range(ROWS)]
    while not check_for_valid_moves(board):
         board = [[random.choice(ITEMS) for _ in range(COLS)] for _ in range(ROWS)]
    return board

def check_matches(board):
    matched = set()
    for r in range(ROWS):
        for c in range(COLS - 2):
            if board[r][c] == board[r][c+1] == board[r][c+2]:
                matched.update([(r, c), (r, c+1), (r, c+2)])
    for r in range(ROWS - 2):
        for c in range(COLS):
            if board[r][c] == board[r+1][c] == board[r+2][c]:
                matched.update([(r, c), (r+1, c), (r+2, c)])
    return matched

def check_for_valid_moves(board):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    temp_board = copy.deepcopy(board)
                    temp_board[r][c], temp_board[nr][nc] = temp_board[nr][nc], temp_board[r][c]
                    if check_matches(temp_board):
                        return True
    return False

def shuffle_board():
    with st.spinner("😵 Tablero bloqueado. Barajando caramelos..."):
        time.sleep(1.5)
    
    new_board = init_board() 
    st.session_state.board = new_board
    st.session_state.selected = None
    st.toast("El tablero ha sido reorganizado. ¡Sigue jugando!", icon="🎲")
    st.rerun()

def eliminate_and_refill(board, matches):
    points = len(matches) * 10
    for c in range(COLS):
        col = [board[r][c] for r in range(ROWS) if (r, c) not in matches]
        missing = ROWS - len(col)
        new_items = [random.choice(ITEMS) for _ in range(missing)]
        final_col = new_items + col
        for r in range(ROWS):
            board[r][c] = final_col[r]
    return points

def next_level():
    with st.spinner(f"🚀 Preparando Nivel {st.session_state.level + 1}... ¡Añadiendo más azúcar!"):
        time.sleep(2.5) 
    
    # 1. Incrementa el nivel
    st.session_state.level += 1
    
    # 2. Mantiene el aumento de movimientos, pero la meta crece más rápido
    st.session_state.moves = BASE_MOVES + (st.session_state.level - 1)
    
    # 3. **CAMBIO CLAVE AQUÍ: Aumenta la dificultad de la meta (1.75)**
    st.session_state.target_score = int(BASE_TARGET * (TARGET_MULTIPLIER ** (st.session_state.level - 1)))
    
    # 4. Reinicia el estado del tablero
    st.session_state.board = init_board() 
    st.session_state.selected = None
    st.session_state.game_state = "PLAYING"
    st.session_state.show_lottie = False 
    st.rerun()

# --- CONTROLADOR DE EVENTOS ---
def handle_click(r, c):
    if st.session_state.game_state != "PLAYING":
        return

    st.session_state.show_lottie = False 

    if st.session_state.selected is None:
        st.session_state.selected = (r, c)
    else:
        r1, c1 = st.session_state.selected
        r2, c2 = r, c
        
        if (abs(r1 - r2) + abs(c1 - c2)) == 1:
            board = st.session_state.board
            board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
            
            matches = check_matches(board)
            if matches:
                st.session_state.moves -= 1
                points = eliminate_and_refill(board, matches)
                st.session_state.score += points
                
                # ACTIVAR ANIMACIÓN DE PUNTOS
                if lottie_success is not None:
                     st.session_state.show_lottie = True 
                st.toast(f"¡Match! +{points} puntos", icon="⭐")

                chain = check_matches(board)
                while chain:
                    points = eliminate_and_refill(board, chain)
                    st.session_state.score += (points * 2) 
                    chain = check_matches(board)
                
                st.session_state.selected = None
                
                if not check_for_valid_moves(board):
                     shuffle_board()

                if st.session_state.score >= st.session_state.target_score:
                    st.session_state.game_state = "LEVEL_COMPLETE"
                    st.rerun()
                elif st.session_state.moves <= 0:
                    st.session_state.game_state = "GAME_OVER"
                    st.rerun()
            else:
                board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
                st.toast("¡Eso no combina! Intenta de nuevo.", icon="🚫")
                st.session_state.selected = None
        
        elif (r1, c1) == (r2, c2):
            st.session_state.selected = None
        else:
            st.session_state.selected = (r, c)


# --- APP PRINCIPAL ---

st.set_page_config(page_title="Super Candy Streamlit", page_icon="🍬", layout="centered")
inject_custom_css()

# Inicialización de Estado
if 'board' not in st.session_state:
    st.session_state.board = init_board()
    st.session_state.score = 0
    st.session_state.level = 1
    # Inicializa con la nueva configuración:
    st.session_state.target_score = BASE_TARGET
    st.session_state.moves = BASE_MOVES 
    st.session_state.selected = None
    st.session_state.game_state = "PLAYING" 
    st.session_state.show_lottie = False 

# --- UI: BARRA LATERAL (st.metric) ---
with st.sidebar:
    st.header("📊 Estadísticas")
    st.metric(label="Nivel Actual", value=f"#{st.session_state.level}")
    
    move_color = "red" if st.session_state.moves < 5 else "green"
    st.metric(label="Movimientos Restantes", value=st.session_state.moves)
    st.metric(label="Puntuación Total", value=st.session_state.score)
    
    st.markdown("---")
    if st.button("🔄 Reiniciar Todo", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- UI: ÁREA PRINCIPAL ---

st.title("🍬 Super Candy Streamlit")

# ******* RENDERIZADO DE ANIMACIÓN DE PUNTOS *******
if st.session_state.get('show_lottie') and lottie_success is not None:
    st_lottie(lottie_success, height=100, width=100, key="success_lottie", speed=1.5)
    st.session_state.show_lottie = False


# PANTALLA 1: JUGANDO
if st.session_state.game_state == "PLAYING":
    
    progress = min(1.0, st.session_state.score / st.session_state.target_score)
    st.progress(progress, text=f"Meta del Nivel: **{st.session_state.target_score}** pts ({int(progress*100)}%)")
    
    board_container = st.container()
    with board_container:
        for r in range(ROWS):
            cols = st.columns(COLS)
            for c in range(COLS):
                emoji = st.session_state.board[r][c]
                is_selected = st.session_state.selected == (r, c)
                display_text = emoji 
                
                cols[c].button(
                    display_text,
                    key=f"{r}_{c}",
                    on_click=handle_click,
                    args=(r, c),
                    use_container_width=True,
                    help="Click para seleccionar, click en adyacente para intercambiar"
                )
                if is_selected:
                    # Hack: Inyecta la clase CSS para la animación de pulsación
                    st.markdown(f"""
                        <script>
                            document.querySelector('[data-testid="stButton"] button[key="{r}_{c}"]').closest('.stButton').classList.add('selected-btn');
                        </script>
                    """, unsafe_allow_html=True)


# PANTALLA 2: NIVEL COMPLETADO 
elif st.session_state.game_state == "LEVEL_COMPLETE":
    st.balloons()
    st.markdown(f"""
    <div style="text-align: center; padding: 40px; background-color: #d1e7dd; border-radius: 20px; border: 2px solid #badbcc;">
        <h1 style="color: #0f5132 !important;">🎉 ¡NIVEL {st.session_state.level} SUPERADO!</h1>
        <h3>Puntuación acumulada: {st.session_state.score}</h3>
        <p>¡Preparate para el Nivel {st.session_state.level + 1}!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("###")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 IR AL SIGUIENTE NIVEL", type="primary", use_container_width=True):
            next_level()

# PANTALLA 3: GAME OVER
elif st.session_state.game_state == "GAME_OVER":
    st.snow()
    st.markdown(f"""
    <div style="text-align: center; padding: 40px; background-color: #f8d7da; border-radius: 20px; border: 2px solid #f5c6cb;">
        <h1 style="color: #842029 !important;">💀 ¡FIN DEL JUEGO!</h1>
        <h3>Llegaste hasta el Nivel {st.session_state.level}</h3>
        <h3>Puntuación final: {st.session_state.score}</h3>
        <p>Te quedaste sin movimientos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("###")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 INTENTAR DE NUEVO", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()