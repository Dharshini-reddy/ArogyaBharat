# ArogyaBharat
A simple student wellness webapp that helps students learn about nutrition, exercise, sleep, hydration and healthy habits, while allowing them to track their daily activities and reminders.
[try.py](https://github.com/user-attachments/files/31526726/try.py)
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

# Always create/use the DB in the same folder as this Python file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "arogya_bharat.db")

USER_ID = 1


# =========================================================
# DATABASE CONNECTION
# =========================================================

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
            fats REAL NOT NULL
        )
    """)

    # ---------------- WATER LOG ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_log (
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            water_liters REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, log_date)
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
            PRIMARY KEY (user_id, log_date)
        )
    """)

    conn.commit()
    conn.close()


# Run database initialization
init_db()


# =========================================================
# FOOD DATABASE FUNCTIONS
# =========================================================

def get_food(log_date=None):

    conn = get_connection()

    if log_date:

        query = """
            SELECT
                log_date AS Date,
                meal AS Meal,
                item AS Item,
                calories AS 'Calories (kcal)',
                protein AS 'Protein (g)',
                carbs AS 'Carbs (g)',
                fats AS 'Fats (g)'
            FROM food_log
            WHERE user_id = ?
            AND log_date = ?
            ORDER BY id DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(USER_ID, log_date)
        )

    else:

        query = """
            SELECT
                log_date AS Date,
                meal AS Meal,
                item AS Item,
                calories AS 'Calories (kcal)',
                protein AS 'Protein (g)',
                carbs AS 'Carbs (g)',
                fats AS 'Fats (g)'
            FROM food_log
            WHERE user_id = ?
            ORDER BY log_date ASC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(USER_ID,)
        )

    conn.close()

    return df


def add_food(log_date, meal, item, cal, protein, carbs, fats):

    conn = get_connection()

    conn.execute("""
        INSERT INTO food_log (
            user_id,
            log_date,
            meal,
            item,
            calories,
            protein,
            carbs,
            fats
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        USER_ID,
        log_date,
        meal,
        item,
        cal,
        protein,
        carbs,
        fats
    ))

    conn.commit()
    conn.close()


# =========================================================
# WATER DATABASE FUNCTIONS
# =========================================================

def get_water(log_date):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT water_liters
        FROM water_log
        WHERE user_id = ?
        AND log_date = ?
    """, (
        USER_ID,
        log_date
    ))

    row = cursor.fetchone()

    conn.close()

    if row:
        return float(row[0])

    return 0.0


def update_water(log_date, amount):

    conn = get_connection()

    conn.execute("""
        INSERT INTO water_log (
            user_id,
            log_date,
            water_liters
        )
        VALUES (?, ?, ?)

        ON CONFLICT(user_id, log_date)
        DO UPDATE SET
            water_liters = water_liters + excluded.water_liters
    """, (
        USER_ID,
        log_date,
        amount
    ))

    conn.commit()
    conn.close()


def reset_water(log_date):

    conn = get_connection()

    conn.execute("""
        UPDATE water_log
        SET water_liters = 0
        WHERE user_id = ?
        AND log_date = ?
    """, (
        USER_ID,
        log_date
    ))

    conn.commit()
    conn.close()


# =========================================================
# HABIT DATABASE FUNCTIONS
# =========================================================

def get_habits(log_date):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sleep_7hrs,
            water_2l,
            post_dinner_walk
        FROM habit_log
        WHERE user_id = ?
        AND log_date = ?
    """, (
        USER_ID,
        log_date
    ))

    row = cursor.fetchone()

    conn.close()

    if row:
        return {
            "sleep": bool(row[0]),
            "water": bool(row[1]),
            "walk": bool(row[2])
        }

    return {
        "sleep": False,
        "water": False,
        "walk": False
    }


def save_habits(log_date, sleep, water, walk):

    conn = get_connection()

    conn.execute("""
        INSERT INTO habit_log (
            user_id,
            log_date,
            sleep_7hrs,
            water_2l,
            post_dinner_walk
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(user_id, log_date)
        DO UPDATE SET
            sleep_7hrs = excluded.sleep_7hrs,
            water_2l = excluded.water_2l,
            post_dinner_walk = excluded.post_dinner_walk
    """, (
        USER_ID,
        log_date,
        int(sleep),
        int(water),
        int(walk)
    ))

    conn.commit()
    conn.close()


# =========================================================
# HEADER
# =========================================================

st.title("🏥 ArogyaBharat")
st.subheader("Smart Health & Preventive Care Platform")

st.caption(
    "Addressing Low Wellness & Nutrition Awareness "
    "in Educational Campuses | SIH 2026"
)

selected_date = st.date_input(
    "📅 Select Date",
    value=date.today()
)

date_str = selected_date.strftime("%Y-%m-%d")

st.divider()


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🥗 Mess Logger",
    "📊 Trends & Risk Advisor",
    "🏋️ Hydration & Habits",
    "🧠 Knowledge Hub"
])


# =========================================================
# TAB 1 - MESS LOGGER
# =========================================================

with tab1:

    st.header(f"🥗 Mess Logger — {date_str}")

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # ADD FOOD
    # -----------------------------------------------------

    with col1:

        st.subheader("➕ Add Food")

        meal = st.selectbox(
            "Meal",
            [
                "Breakfast",
                "Lunch",
                "Snacks",
                "Dinner"
            ]
        )

        presets = {

            "Custom": {
                "cal": 0,
                "p": 0,
                "c": 0,
                "f": 0
            },

            "Oats Porridge": {
                "cal": 150,
                "p": 5,
                "c": 27,
                "f": 3
            },

            "Boiled Egg": {
                "cal": 78,
                "p": 6,
                "c": 0.6,
                "f": 5
            },

            "Rice": {
                "cal": 215,
                "p": 5,
                "c": 45,
                "f": 1.6
            },

            "Dal Tadka": {
                "cal": 180,
                "p": 9,
                "c": 20,
                "f": 6
            },

            "Paneer Curry": {
                "cal": 260,
                "p": 12,
                "c": 8,
                "f": 20
            },

            "Chapati": {
                "cal": 104,
                "p": 3,
                "c": 15,
                "f": 3
            }
        }

        item_sel = st.selectbox(
            "Food Item",
            list(presets.keys())
        )

        if item_sel == "Custom":

            item = st.text_input(
                "Item Name",
                "Paneer Wrap"
            )

            cal = st.number_input(
                "Calories",
                min_value=0.0,
                max_value=1500.0,
                value=200.0
            )

            protein = st.number_input(
                "Protein (g)",
                min_value=0.0,
                max_value=100.0,
                value=10.0
            )

            carbs = st.number_input(
                "Carbs (g)",
                min_value=0.0,
                max_value=200.0,
                value=30.0
            )

            fats = st.number_input(
                "Fats (g)",
                min_value=0.0,
                max_value=100.0,
                value=5.0
            )

        else:

            item = item_sel

            cal = presets[item_sel]["cal"]
            protein = presets[item_sel]["p"]
            carbs = presets[item_sel]["c"]
            fats = presets[item_sel]["f"]

        if st.button(
            "➕ Log Food",
            use_container_width=True
        ):

            add_food(
                date_str,
                meal,
                item,
                cal,
                protein,
                carbs,
                fats
            )

            st.success(
                f"{item} added successfully!"
            )

            st.rerun()

    # -----------------------------------------------------
    # DAILY INTAKE
    # -----------------------------------------------------

    with col2:

        st.subheader("📋 Daily Intake")

        df_today = get_food(date_str)

        if not df_today.empty:

            st.dataframe(
                df_today.drop(columns=["Date"]),
                use_container_width=True,
                hide_index=True
            )

            total_calories = df_today[
                "Calories (kcal)"
            ].sum()

            total_protein = df_today[
                "Protein (g)"
            ].sum()

            total_carbs = df_today[
                "Carbs (g)"
            ].sum()

            total_fats = df_today[
                "Fats (g)"
            ].sum()

            m1, m2, m3, m4 = st.columns(4)

            m1.metric(
                "Calories",
                f"{total_calories:.0f} kcal"
            )

            m2.metric(
                "Protein",
                f"{total_protein:.1f} g"
            )

            m3.metric(
                "Carbs",
                f"{total_carbs:.1f} g"
            )

            m4.metric(
                "Fats",
                f"{total_fats:.1f} g"
            )

            fig = px.pie(
                names=[
                    "Protein",
                    "Carbs",
                    "Fats"
                ],
                values=[
                    total_protein,
                    total_carbs,
                    total_fats
                ],
                title="Macro Breakdown"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "No food logged for this date."
            )


# =========================================================
# TAB 2 - ANALYTICS
# =========================================================

with tab2:

    st.header("📊 Analytics & Preventive Advice")

    df_all = get_food()

    if not df_all.empty:

        df_trend = (
            df_all
            .groupby("Date")["Calories (kcal)"]
            .sum()
            .reset_index()
        )

        fig_line = px.line(
            df_trend,
            x="Date",
            y="Calories (kcal)",
            markers=True,
            title="Calorie Trend Over Time"
        )

        st.plotly_chart(
            fig_line,
            use_container_width=True
        )

    else:

        st.info(
            "Start logging meals to see your calorie trends."
        )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:

        st.subheader("📏 Body Metrics")

        w = st.number_input(
            "Weight (kg)",
            min_value=30.0,
            max_value=150.0,
            value=68.0
        )

        h = st.number_input(
            "Height (cm)",
            min_value=120.0,
            max_value=220.0,
            value=172.0
        )

        sleep = st.slider(
            "Nightly Sleep (hrs)",
            min_value=3.0,
            max_value=10.0,
            value=7.0,
            step=0.5
        )

    with col_b:

        st.subheader("🔎 Wellness Indicators")

        bmi = w / ((h / 100) ** 2)

        st.metric(
            "BMI",
            f"{bmi:.1f}"
        )

        st.caption(
            "BMI is only a general screening measure and "
            "should not be treated as a diagnosis."
        )

        if sleep < 7:

            st.warning(
                "😴 Your recorded sleep is below 7 hours. "
                "Try maintaining a consistent sleep schedule."
            )

        else:

            st.success(
                "😴 Good job maintaining 7+ hours of sleep!"
            )


# =========================================================
# TAB 3 - HYDRATION & HABITS
# =========================================================

with tab3:

    st.header(
        f"🏋️ Hydration & Habits — {date_str}"
    )

    col_w, col_h = st.columns(2)

    # -----------------------------------------------------
    # WATER
    # -----------------------------------------------------

    with col_w:

        current_w = get_water(date_str)

        st.subheader(
            f"💧 Water Intake: {current_w:.2f} L"
        )

        if st.button(
            "🥤 Drink Glass — 250 ml",
            use_container_width=True
        ):

            update_water(
                date_str,
                0.25
            )

            st.rerun()

        if st.button(
            "🔄 Reset Water",
            use_container_width=True
        ):

            reset_water(date_str)

            st.rerun()

        fig_g = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=current_w,
                title={
                    "text": "Daily Water Intake"
                },
                gauge={
                    "axis": {
                        "range": [0, 3.5]
                    }
                }
            )
        )

        st.plotly_chart(
            fig_g,
            use_container_width=True
        )

    # -----------------------------------------------------
    # HABITS
    # -----------------------------------------------------

    with col_h:

        st.subheader("✅ Preventive Checklist")

        # Load saved values from database
        saved_habits = get_habits(date_str)

        q1 = st.checkbox(
            "7+ hrs sleep",
            value=saved_habits["sleep"],
            key=f"sleep_{date_str}"
        )

        q2 = st.checkbox(
            "Drank 2L+ water",
            value=saved_habits["water"],
            key=f"water_{date_str}"
        )

        q3 = st.checkbox(
            "Post-dinner walk",
            value=saved_habits["walk"],
            key=f"walk_{date_str}"
        )

        completed = sum([
            q1,
            q2,
            q3
        ])

        st.progress(
            completed / 3
        )

        st.write(
            f"Completed: **{completed}/3** habits"
        )

        if st.button(
            "💾 Save Today's Habits",
            use_container_width=True
        ):

            save_habits(
                date_str,
                q1,
                q2,
                q3
            )

            st.success(
                "Today's habits have been saved permanently."
            )

            st.rerun()


# =========================================================
# TAB 4 - KNOWLEDGE HUB
# =========================================================

with tab4:

    st.header(
        "🧠 Preventive Health Knowledge Hub"
    )

    with st.expander(
        "🎓 Hostel Diet Hacks"
    ):

        st.write(
            "Choose balanced meals with vegetables, "
            "dal, eggs, fruits, sprouts and whole grains. "
            "Limit frequent fried and highly processed foods."
        )

    with st.expander(
        "😴 Sleep Optimization"
    ):

        st.write(
            "Maintain a regular sleep schedule and reduce "
            "screen use before bedtime."
        )

    with st.expander(
        "💧 Hydration"
    ):

        st.write(
            "Keep water accessible during classes and "
            "activities. Individual fluid needs can vary."
        )

    with st.expander(
        "🏃 Healthy Movement"
    ):

        st.write(
            "Include regular movement throughout the day, "
            "such as walking between classes or taking "
            "active breaks from prolonged sitting."
        )


# =========================================================
# DATABASE LOCATION
# =========================================================

with st.sidebar:

    st.header("⚙️ App Information")

    st.success(
        "Data storage: SQLite"
    )

    st.write(
        "Database:"
    )

    st.code(
        DB_FILE
    )

    st.caption(
        "Food, water and habit data are stored "
        "in the local SQLite database."
    )
