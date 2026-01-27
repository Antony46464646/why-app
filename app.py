import streamlit as st
import sqlite3
from datetime import datetime
import hashlib

st.set_page_config(page_title="WHY", layout="centered")

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("progress.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password_hash TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    session_id TEXT PRIMARY KEY,
    stage TEXT,
    stage1 TEXT,
    stage2 TEXT,
    updated_at TEXT
)
""")
conn.commit()

# -----------------------------
# AUTH HELPERS
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password):
    try:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (email, hash_password(password), datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(email, password):
    cursor.execute(
        "SELECT password_hash FROM users WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    if not row:
        return False
    return row[0] == hash_password(password)

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(id(st.session_state))

# -----------------------------
# LOGIN / REGISTER UI
# -----------------------------
if not st.session_state.logged_in:
    st.title("WHY")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.session_state.auth_mode == "login":
        if st.button("Login"):
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid email or password")

        if st.button("Create new account"):
            st.session_state.auth_mode = "register"
            st.rerun()

    else:
        if st.button("Register"):
            if create_user(email, password):
                st.success("Account created. Please log in.")
                st.session_state.auth_mode = "login"
                st.rerun()
            else:
                st.error("Email already exists")

        if st.button("Back to login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    st.stop()

# -----------------------------
# LOAD PROGRESS (UNCHANGED)
# -----------------------------
cursor.execute(
    "SELECT stage, stage1, stage2 FROM progress WHERE session_id = ?",
    (st.session_state.session_id,)
)
row = cursor.fetchone()

if row:
    st.session_state.stage = row[0]
    st.session_state.first_reflection = row[1]
    st.session_state.self_reflection = row[2]
else:
    if "stage" not in st.session_state:
        st.session_state.stage = "landing"

# -----------------------------
# SAVE / RESET
# -----------------------------
def save_progress():
    cursor.execute("""
        INSERT OR REPLACE INTO progress
        VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.session_id,
        st.session_state.stage,
        st.session_state.get("first_reflection"),
        st.session_state.get("self_reflection"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()

def reset_journey():
    cursor.execute(
        "DELETE FROM progress WHERE session_id = ?",
        (st.session_state.session_id,)
    )
    conn.commit()

    for k in ["stage", "first_reflection", "self_reflection"]:
        if k in st.session_state:
            del st.session_state[k]

    st.session_state.stage = "landing"
    st.rerun()

# -----------------------------
# APP FLOW (SAME AS BEFORE)
# -----------------------------
if st.session_state.stage == "landing":
    st.title("WHY")
    st.write("The universe has questions. So do you.")

    if st.button("Begin"):
        st.session_state.stage = "arrival"
        save_progress()
        st.rerun()

elif st.session_state.stage == "arrival":
    st.subheader("Stage 1 · Arrival")
    user_input = st.text_area("What brought you here today?", height=150)

    if st.button("Continue"):
        if user_input.strip():
            st.session_state.first_reflection = user_input
            st.session_state.stage = "reflection"
            save_progress()
            st.rerun()

elif st.session_state.stage == "reflection":
    st.subheader("Reflection")
    st.info(st.session_state.first_reflection)

    if st.button("Continue deeper"):
        st.session_state.stage = "self"
        save_progress()
        st.rerun()

elif st.session_state.stage == "self":
    st.subheader("Stage 2 · Self")
    self_input = st.text_area("What feels most present right now?", height=150)

    if st.button("Continue"):
        if self_input.strip():
            st.session_state.self_reflection = self_input
            st.session_state.stage = "pause"
            save_progress()
            st.rerun()

elif st.session_state.stage == "pause":
    st.subheader("Pause")
    st.write("You’ve gone far enough for now.")

    if st.button("Start a new journey"):
        reset_journey()
