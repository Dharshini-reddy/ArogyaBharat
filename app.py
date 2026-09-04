import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import sqlite3
import os

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ArogyaBharat | SIH 2026",
    page_icon="🏥",
    layout="wide"
)

# =========================================================
# DATABASE CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "arogya_bharat.db")

WORKOUT_PLANS = {
    "Beginner Full Body": {"minutes": 25, "description": "A gentle strength and mobility session for building a consistent routine.", "exercises": [("Warm-up walk or march", "Warm-up", "5 minutes", 5), ("Bodyweight squats", "Strength", "3 sets × 10 reps", 6), ("Incline or knee push-ups", "Strength", "3 sets × 8 reps", 6), ("Glute bridges", "Strength", "3 sets × 12 reps", 5), ("Standing stretch", "Cool-down", "3 minutes", 3)]},
    "Cardio & Stamina": {"minutes": 30, "description": "A no-equipment cardio session that can be adapted to your pace.", "exercises": [("Dynamic warm-up", "Warm-up", "5 minutes", 5), ("Brisk walk / jog intervals", "Cardio", "15 minutes", 15), ("Jumping jacks or step jacks", "Cardio", "3 sets × 30 seconds", 3), ("Slow walk", "Cool-down", "4 minutes", 4), ("Calf and hamstring stretch", "Cool-down", "3 minutes", 3)]},
    "Yoga & Recovery": {"minutes": 20, "description": "A low-impact mobility and recovery flow for busy study days.", "exercises": [("Breathing and neck mobility", "Warm-up", "3 minutes", 3), ("Sun salutations", "Mobility", "5 rounds", 7), ("Cat-cow and child’s pose", "Mobility", "4 minutes", 4), ("Seated forward fold", "Mobility", "3 minutes", 3), ("Relaxation breathing", "Cool-down", "3 minutes", 3)]},
}

MOTIVATION_QUOTES = [
    "Consistency beats intensity. A small session today is a win.",
    "You do not need to be perfect — you only need to keep showing up.",
    "Your future energy is built by the choices you make today.",
    "Movement is a celebration of what your body can do.",
    "One healthy decision can change the direction of your whole day.",
]

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# =========================================================
# DATABASE INITIALIZATION
# =========================================================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- USERS TABLE ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ---------------- FOOD LOG ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            meal TEXT NOT NULL,
            item TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fats REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # ---------------- WATER LOG ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_log (
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            water_liters REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # ---------------- HABITS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_log (
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            sleep_7hrs INTEGER NOT NULL DEFAULT 0,
            water_2l INTEGER NOT NULL DEFAULT 0,
            post_dinner_walk INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, workout_date TEXT NOT NULL,
            plan_name TEXT NOT NULL, total_minutes INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, workout_date), FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_exercise_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL, exercise_name TEXT NOT NULL,
            category TEXT NOT NULL, target TEXT NOT NULL, estimated_minutes INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0, completed_at TEXT,
            FOREIGN KEY (session_id) REFERENCES workout_sessions (id) ON DELETE CASCADE
        )
    """)

    # A short daily commitment makes motivation actionable, rather than only a quote.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fitness_checkins (
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            intention TEXT NOT NULL DEFAULT 'Move for at least 10 minutes',
            committed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, checkin_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================================================
# AUTHENTICATION FUNCTIONS
# =========================================================
def register_user(username, password):
    try:
        conn = get_connection()
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# =========================================================
# DATABASE CRUD FUNCTIONS (Updated to require user_id)
# =========================================================
def get_food(user_id, log_date=None):
    conn = get_connection()
    if log_date:
        query = """
            SELECT log_date AS Date, meal AS Meal, item AS Item, calories AS 'Calories (kcal)',
                   protein AS 'Protein (g)', carbs AS 'Carbs (g)', fats AS 'Fats (g)'
            FROM food_log WHERE user_id = ? AND log_date = ? ORDER BY id DESC
        """
        df = pd.read_sql_query(query, conn, params=(user_id, log_date))
    else:
        query = """
            SELECT log_date AS Date, meal AS Meal, item AS Item, calories AS 'Calories (kcal)',
                   protein AS 'Protein (g)', carbs AS 'Carbs (g)', fats AS 'Fats (g)'
            FROM food_log WHERE user_id = ? ORDER BY log_date ASC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def add_food(user_id, log_date, meal, item, cal, protein, carbs, fats):
    conn = get_connection()
    conn.execute("""
        INSERT INTO food_log (user_id, log_date, meal, item, calories, protein, carbs, fats)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, log_date, meal, item, cal, protein, carbs, fats))
    conn.commit()
    conn.close()

def get_water(user_id, log_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT water_liters FROM water_log WHERE user_id = ? AND log_date = ?", (user_id, log_date))
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 0.0

def update_water(user_id, log_date, amount):
    conn = get_connection()
    conn.execute("""
        INSERT INTO water_log (user_id, log_date, water_liters) VALUES (?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET water_liters = water_liters + excluded.water_liters
    """, (user_id, log_date, amount))
    conn.commit()
    conn.close()

def reset_water(user_id, log_date):
    conn = get_connection()
    conn.execute("UPDATE water_log SET water_liters = 0 WHERE user_id = ? AND log_date = ?", (user_id, log_date))
    conn.commit()
    conn.close()

def get_habits(user_id, log_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sleep_7hrs, water_2l, post_dinner_walk FROM habit_log WHERE user_id = ? AND log_date = ?", (user_id, log_date))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"sleep": bool(row[0]), "water": bool(row[1]), "walk": bool(row[2])}
    return {"sleep": False, "water": False, "walk": False}

def save_habits(user_id, log_date, sleep, water, walk):
    conn = get_connection()
    conn.execute("""
        INSERT INTO habit_log (user_id, log_date, sleep_7hrs, water_2l, post_dinner_walk)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET
            sleep_7hrs = excluded.sleep_7hrs,
            water_2l = excluded.water_2l,
            post_dinner_walk = excluded.post_dinner_walk
    """, (user_id, log_date, int(sleep), int(water), int(walk)))
    conn.commit()
    conn.close()

def get_workout_session(user_id, workout_date):
    conn = get_connection()
    row = conn.execute("SELECT id, plan_name, total_minutes FROM workout_sessions WHERE user_id = ? AND workout_date = ?", (user_id, workout_date)).fetchone()
    conn.close()
    return row

def start_workout_plan(user_id, workout_date, plan_name):
    plan = WORKOUT_PLANS[plan_name]
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO workout_sessions (user_id, workout_date, plan_name, total_minutes) VALUES (?, ?, ?, ?)", (user_id, workout_date, plan_name, plan["minutes"]))
        session_id = cursor.lastrowid
        cursor.executemany("INSERT INTO workout_exercise_log (session_id, exercise_name, category, target, estimated_minutes) VALUES (?, ?, ?, ?, ?)", [(session_id, name, category, target, minutes) for name, category, target, minutes in plan["exercises"]])
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_workout_exercises(session_id):
    conn = get_connection()
    rows = conn.execute("SELECT id, exercise_name, category, target, estimated_minutes, completed FROM workout_exercise_log WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
    conn.close()
    return rows

def update_workout_exercise(exercise_id, completed):
    conn = get_connection()
    conn.execute("UPDATE workout_exercise_log SET completed = ?, completed_at = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END WHERE id = ?", (int(completed), int(completed), exercise_id))
    conn.commit()
    conn.close()

def get_workout_stats(user_id):
    conn = get_connection()
    row = conn.execute("""SELECT
        (SELECT COUNT(*) FROM workout_sessions WHERE user_id = ?),
        (SELECT COALESCE(SUM(total_minutes), 0) FROM workout_sessions WHERE user_id = ?),
        COALESCE(SUM(CASE WHEN e.completed = 1 THEN e.estimated_minutes ELSE 0 END), 0)
        FROM workout_sessions s LEFT JOIN workout_exercise_log e ON e.session_id = s.id WHERE s.user_id = ?""", (user_id, user_id, user_id)).fetchone()
    conn.close()
    return row

# =========================================================
# FITNESS COACH / MOTIVATION FUNCTIONS
# =========================================================
def get_fitness_checkin(user_id, checkin_date):
    conn = get_connection()
    row = conn.execute("SELECT intention, committed FROM fitness_checkins WHERE user_id = ? AND checkin_date = ?", (user_id, checkin_date)).fetchone()
    conn.close()
    return row

def save_fitness_checkin(user_id, checkin_date, intention):
    conn = get_connection()
    conn.execute("""
        INSERT INTO fitness_checkins (user_id, checkin_date, intention, committed, updated_at)
        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, checkin_date) DO UPDATE SET
            intention = excluded.intention, committed = 1, updated_at = CURRENT_TIMESTAMP
    """, (user_id, checkin_date, intention))
    conn.commit()
    conn.close()

def get_workout_streak(user_id, today):
    """Count consecutive calendar days with a fully completed saved workout."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.workout_date
        FROM workout_sessions s JOIN workout_exercise_log e ON e.session_id = s.id
        WHERE s.user_id = ?
        GROUP BY s.id
        HAVING COUNT(e.id) > 0 AND SUM(e.completed) = COUNT(e.id)
    """, (user_id,)).fetchall()
    conn.close()
    completed_dates = {date.fromisoformat(row[0]) for row in rows}
    streak, cursor_day = 0, today
    while cursor_day in completed_dates:
        streak += 1
        cursor_day = date.fromordinal(cursor_day.toordinal() - 1)
    return streak

def get_daily_fitness_wins(user_id, log_date):
    """Return evidence-based daily wins from the app's saved health records."""
    water_win = get_water(user_id, log_date) >= 2.0
    habits = get_habits(user_id, log_date)
    food_win = not get_food(user_id, log_date).empty
    session = get_workout_session(user_id, log_date)
    workout_win = False
    if session:
        exercises = get_workout_exercises(session[0])
        workout_win = bool(exercises) and all(bool(exercise[5]) for exercise in exercises)
    return {
        "Balanced meals logged": food_win,
        "2L hydration reached": water_win,
        "Healthy habit completed": any(habits.values()),
        "Workout completed": workout_win,
    }

# =========================================================
# SESSION STATE & LOGIN UI
# =========================================================
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.title("🏥 ArogyaBharat - Login")
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    
    with tab_login:
        login_user_input = st.text_input("Username", key="login_user")
        login_pass_input = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            user = login_user(login_user_input, login_pass_input)
            if user:
                st.session_state["user"] = {"id": user[0], "username": user[1]}
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    with tab_signup:
        reg_user_input = st.text_input("New Username", key="reg_user")
        reg_pass_input = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            if reg_user_input and reg_pass_input:
                if register_user(reg_user_input, reg_pass_input):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already taken.")
            else:
                st.warning("Please fill out all fields.")
    
    st.stop() # Halts page rendering here if not logged in

# Extract active user variables for the main app
ACTIVE_USER_ID = st.session_state["user"]["id"]
ACTIVE_USERNAME = st.session_state["user"]["username"]

# =========================================================
# SIDEBAR / LOGOUT
# =========================================================
with st.sidebar:
    st.header(f"👋 Welcome, {ACTIVE_USERNAME}")
    if st.button("Logout"):
        st.session_state["user"] = None
        st.rerun()
        
    st.divider()
    st.header("⚙️ App Information")
    st.success("Data storage: SQLite")
    st.write("Database:")
    st.code(DB_FILE)
    st.caption("Food, water and habit data are stored safely.")

# =========================================================
# HEADER
# =========================================================
st.title("🏥 ArogyaBharat")
st.subheader("Smart Health & Preventive Care Platform")
st.caption("Addressing Low Wellness & Nutrition Awareness in Educational Campuses | SIH 2026")

selected_date = st.date_input("📅 Select Date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")
st.divider()

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🥗 Mess Logger", "📊 Trends & Risk Advisor", "💧 Hydration & Habits", "🏋️ Workouts", "✨ Fit Coach", "🧠 Knowledge Hub"])

# =========================================================
# TAB 1 - MESS LOGGER
# =========================================================
with tab1:
    st.header(f"🥗 Mess Logger — {date_str}")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("➕ Add Food")
        meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Snacks", "Dinner"])
        presets = {
            "Custom": {"cal": 0, "p": 0, "c": 0, "f": 0},
            "Oats Porridge": {"cal": 150, "p": 5, "c": 27, "f": 3},
            "Boiled Egg": {"cal": 78, "p": 6, "c": 0.6, "f": 5},
            "Rice": {"cal": 215, "p": 5, "c": 45, "f": 1.6},
            "Dal Tadka": {"cal": 180, "p": 9, "c": 20, "f": 6},
            "Paneer Curry": {"cal": 260, "p": 12, "c": 8, "f": 20},
            "Chapati": {"cal": 104, "p": 3, "c": 15, "f": 3}
        }
        item_sel = st.selectbox("Food Item", list(presets.keys()))

        if item_sel == "Custom":
            item = st.text_input("Item Name", "Paneer Wrap")
            cal = st.number_input("Calories", min_value=0.0, max_value=1500.0, value=200.0)
            protein = st.number_input("Protein (g)", min_value=0.0, max_value=100.0, value=10.0)
            carbs = st.number_input("Carbs (g)", min_value=0.0, max_value=200.0, value=30.0)
            fats = st.number_input("Fats (g)", min_value=0.0, max_value=100.0, value=5.0)
        else:
            item = item_sel
            cal = presets[item_sel]["cal"]
            protein = presets[item_sel]["p"]
            carbs = presets[item_sel]["c"]
            fats = presets[item_sel]["f"]

        if st.button("➕ Log Food", use_container_width=True):
            add_food(ACTIVE_USER_ID, date_str, meal, item, cal, protein, carbs, fats)
            st.success(f"{item} added successfully!")
            st.rerun()

    with col2:
        st.subheader("📋 Daily Intake")
        df_today = get_food(ACTIVE_USER_ID, date_str)

        if not df_today.empty:
            st.dataframe(df_today.drop(columns=["Date"]), use_container_width=True, hide_index=True)
            total_calories = df_today["Calories (kcal)"].sum()
            total_protein = df_today["Protein (g)"].sum()
            total_carbs = df_today["Carbs (g)"].sum()
            total_fats = df_today["Fats (g)"].sum()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Calories", f"{total_calories:.0f} kcal")
            m2.metric("Protein", f"{total_protein:.1f} g")
            m3.metric("Carbs", f"{total_carbs:.1f} g")
            m4.metric("Fats", f"{total_fats:.1f} g")

            fig = px.pie(names=["Protein", "Carbs", "Fats"], values=[total_protein, total_carbs, total_fats], title="Macro Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No food logged for this date.")

# =========================================================
# TAB 2 - ANALYTICS
# =========================================================
with tab2:
    st.header("📊 Analytics & Preventive Advice")
    df_all = get_food(ACTIVE_USER_ID)

    if not df_all.empty:
        df_trend = df_all.groupby("Date")["Calories (kcal)"].sum().reset_index()
        fig_line = px.line(df_trend, x="Date", y="Calories (kcal)", markers=True, title="Calorie Trend Over Time")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Start logging meals to see your calorie trends.")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📏 Body Metrics")
        w = st.number_input("Weight (kg)", min_value=30.0, max_value=150.0, value=68.0)
        h = st.number_input("Height (cm)", min_value=120.0, max_value=220.0, value=172.0)
        sleep = st.slider("Nightly Sleep (hrs)", min_value=3.0, max_value=10.0, value=7.0, step=0.5)

    with col_b:
        st.subheader("🔎 Wellness Indicators")
        bmi = w / ((h / 100) ** 2)
        st.metric("BMI", f"{bmi:.1f}")
        st.caption("BMI is only a general screening measure and should not be treated as a diagnosis.")

        if sleep < 7:
            st.warning("😴 Your recorded sleep is below 7 hours. Try maintaining a consistent sleep schedule.")
        else:
            st.success("😴 Good job maintaining 7+ hours of sleep!")

# =========================================================
# TAB 3 - HYDRATION & HABITS
# =========================================================
with tab3:
    st.header(f"🏋️ Hydration & Habits — {date_str}")
    col_w, col_h = st.columns(2)

    with col_w:
        current_w = get_water(ACTIVE_USER_ID, date_str)
        st.subheader(f"💧 Water Intake: {current_w:.2f} L")
        if st.button("🥤 Drink Glass — 250 ml", use_container_width=True):
            update_water(ACTIVE_USER_ID, date_str, 0.25)
            st.rerun()

        if st.button("🔄 Reset Water", use_container_width=True):
            reset_water(ACTIVE_USER_ID, date_str)
            st.rerun()

        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=current_w, title={"text": "Daily Water Intake"}, gauge={"axis": {"range": [0, 3.5]}}))
        st.plotly_chart(fig_g, use_container_width=True)

    with col_h:
        st.subheader("✅ Preventive Checklist")
        saved_habits = get_habits(ACTIVE_USER_ID, date_str)

        q1 = st.checkbox("7+ hrs sleep", value=saved_habits["sleep"], key=f"sleep_{date_str}")
        q2 = st.checkbox("Drank 2L+ water", value=saved_habits["water"], key=f"water_{date_str}")
        q3 = st.checkbox("Post-dinner walk", value=saved_habits["walk"], key=f"walk_{date_str}")

        completed = sum([q1, q2, q3])
        st.progress(completed / 3)
        st.write(f"Completed: **{completed}/3** habits")

        if st.button("💾 Save Today's Habits", use_container_width=True):
            save_habits(ACTIVE_USER_ID, date_str, q1, q2, q3)
            st.success("Today's habits have been saved permanently.")
            st.rerun()

# =========================================================
# TAB 4 - WORKOUT SYSTEM
# =========================================================
with tab4:
    st.header(f"🏋️ Workout Planner — {date_str}")
    st.caption("Choose one plan for the day, follow each exercise, and save your progress permanently.")
    session_row = get_workout_session(ACTIVE_USER_ID, date_str)
    if session_row is None:
        left, right = st.columns([1.05, 1])
        with left:
            selected_plan = st.selectbox("Choose today’s workout", list(WORKOUT_PLANS.keys()))
            plan = WORKOUT_PLANS[selected_plan]
            st.subheader(selected_plan)
            st.write(plan["description"])
            st.metric("Estimated duration", f"{plan['minutes']} min")
            if st.button("▶ Start this workout", type="primary", use_container_width=True):
                if start_workout_plan(ACTIVE_USER_ID, date_str, selected_plan):
                    st.success("Workout created. Tick exercises as you complete them.")
                    st.rerun()
                else:
                    st.warning("A workout is already planned for this date.")
        with right:
            st.subheader("Today’s exercise preview")
            for exercise, category, target, minutes in plan["exercises"]:
                st.write(f"**{exercise}** · {target}")
                st.caption(f"{category} · about {minutes} min")
    else:
        session_id, plan_name, total_minutes = session_row
        exercises = get_workout_exercises(session_id)
        completed_count = sum(bool(exercise[5]) for exercise in exercises)
        completed_minutes = sum(exercise[4] for exercise in exercises if exercise[5])
        c1, c2, c3 = st.columns(3)
        c1.metric("Today’s plan", plan_name)
        c2.metric("Progress", f"{completed_count}/{len(exercises)} exercises")
        c3.metric("Movement completed", f"{completed_minutes}/{total_minutes} min")
        st.progress(completed_count / len(exercises) if exercises else 0)
        st.subheader("Exercise checklist")
        for exercise_id, exercise_name, category, target, estimated_minutes, completed in exercises:
            current = st.checkbox(f"{exercise_name} — {target}", value=bool(completed), key=f"workout_{exercise_id}", help=f"{category} · approximately {estimated_minutes} minutes")
            if current != bool(completed):
                update_workout_exercise(exercise_id, current)
                st.rerun()
        if completed_count == len(exercises):
            st.success("🎉 Workout complete! Great job showing up for your health.")
    stats = get_workout_stats(ACTIVE_USER_ID)
    st.divider()
    st.subheader("Your workout consistency")
    s1, s2, s3 = st.columns(3)
    s1.metric("Plans started", stats[0])
    s2.metric("Minutes planned", f"{stats[1]} min")
    s3.metric("Minutes completed", f"{stats[2]} min")
    st.info("Work within your comfort level. Stop if you feel pain, dizziness, or unwell, and seek professional advice for injuries or medical conditions.")

# =========================================================
# TAB 5 - FITNESS COACH AND MOTIVATION
# =========================================================
with tab5:
    st.header("✨ Fit Coach — Your Daily Motivation")
    st.caption("Build momentum through small commitments and evidence-based progress.")

    quote = MOTIVATION_QUOTES[selected_date.toordinal() % len(MOTIVATION_QUOTES)]
    st.info(f"💬 **Today’s reminder:** {quote}")

    checkin = get_fitness_checkin(ACTIVE_USER_ID, date_str)
    default_intention = checkin[0] if checkin else "Move for at least 10 minutes"
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Make a promise to yourself")
        intention = st.selectbox(
            "My fitness commitment for today",
            ["Move for at least 10 minutes", "Finish today’s workout", "Take an active break between classes", "Drink 2L of water", "Go for a post-dinner walk"],
            index=["Move for at least 10 minutes", "Finish today’s workout", "Take an active break between classes", "Drink 2L of water", "Go for a post-dinner walk"].index(default_intention) if default_intention in ["Move for at least 10 minutes", "Finish today’s workout", "Take an active break between classes", "Drink 2L of water", "Go for a post-dinner walk"] else 0
        )
        if checkin and checkin[1]:
            st.success(f"✅ You committed to: **{checkin[0]}**")
        if st.button("💪 Commit to today’s goal", type="primary", use_container_width=True):
            save_fitness_checkin(ACTIVE_USER_ID, date_str, intention)
            st.balloons()
            st.success("Commitment saved. Your next small action matters!")
            st.rerun()
    with right:
        streak = get_workout_streak(ACTIVE_USER_ID, selected_date)
        st.subheader("Your momentum")
        st.metric("Workout streak", f"{streak} day{'s' if streak != 1 else ''}", help="Consecutive days with all exercises in a saved workout completed.")
        if streak >= 7:
            st.success("🌟 Weekly Warrior badge unlocked!")
        elif streak >= 3:
            st.success("🔥 You are building a powerful routine.")
        else:
            st.write("Complete today’s workout to begin a streak.")

    st.divider()
    st.subheader("Today’s real progress")
    wins = get_daily_fitness_wins(ACTIVE_USER_ID, date_str)
    win_count = sum(wins.values())
    st.progress(win_count / len(wins))
    st.write(f"**{win_count}/{len(wins)} healthy wins** logged today")
    win_cols = st.columns(4)
    for column, (label, achieved) in zip(win_cols, wins.items()):
        column.metric(label, "✓ Done" if achieved else "Next step")
    if win_count == len(wins):
        st.success("🏆 Daily Balance badge unlocked! You took care of movement, hydration, habits, and nutrition today.")
    elif win_count >= 2:
        st.success("You are making progress. Choose one small next step to strengthen your day.")
    else:
        st.warning("Start with the easiest win: drink a glass of water, log a meal, or take a 10-minute walk.")

# =========================================================
# TAB 6 - KNOWLEDGE HUB
# =========================================================
with tab6:
    st.header("🧠 Preventive Health Knowledge Hub")
    with st.expander("🎓 Hostel Diet Hacks"):
        st.write("Choose balanced meals with vegetables, dal, eggs, fruits, sprouts and whole grains. Limit frequent fried and highly processed foods.")
    with st.expander("😴 Sleep Optimization"):
        st.write("Maintain a regular sleep schedule and reduce screen use before bedtime.")
    with st.expander("💧 Hydration"):
        st.write("Keep water accessible during classes and activities. Individual fluid needs can vary.")
    with st.expander("🏃 Healthy Movement"):
        st.write("Include regular movement throughout the day, such as walking between classes or taking active breaks from prolonged sitting.")
