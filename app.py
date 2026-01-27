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
CREATE TABLE IF NOT EXISTS auth_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    email TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    user_email TEXT PRIMARY KEY,
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
    return row and row[0] == hash_password(password)

def set_logged_in(email):
    cursor.execute(
        "INSERT OR REPLACE INTO auth_state (id, email) VALUES (1, ?)",
        (email,)
    )
    conn.commit()

def get_logged_in():
    cursor.execute("SELECT email FROM auth_state WHERE id = 1")
    row = cursor.fetchone()
    return row[0] if row else None

def logout_user():
    cursor.execute("DELETE FROM auth_state WHERE id = 1")
    conn.commit()

# -----------------------------
# DB HELPER (RESTORE PROGRESS)
# -----------------------------
def load_user_progress(email):
    cursor.execute(
        "SELECT stage, stage1, stage2 FROM progress WHERE user_email = ?",
        (email,)
    )
    row = cursor.fetchone()
    if row:
        st.session_state.stage = row[0]
        st.session_state.first_reflection = row[1]
        st.session_state.self_reflection = row[2]
    else:
        st.session_state.stage = "landing"

# -----------------------------
# SESSION
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = get_logged_in()

# -----------------------------
# LOGIN / REGISTER
# -----------------------------
if not st.session_state.user_email:
    st.title("WHY")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(email, password):
            set_logged_in(email)
            st.session_state.user_email = email
            st.session_state.pop("stage", None)
            st.rerun()
        else:
            st.error("Invalid email or password")

    st.divider()

    if st.button("Create new account"):
        if create_user(email, password):
            st.success("Account created. Please log in.")
        else:
            st.error("Email already exists")

    st.stop()

# -----------------------------
# LOGOUT
# -----------------------------
if st.button("Logout"):
    logout_user()
    st.session_state.clear()
    st.rerun()

# -----------------------------
# ENTRY / RESTORE (FIXED)
# -----------------------------
if "stage" not in st.session_state:
    load_user_progress(st.session_state.user_email)

# -----------------------------
# SAVE / RESET
# -----------------------------
def save_progress():
    cursor.execute("""
        INSERT OR REPLACE INTO progress
        VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.user_email,
        st.session_state.stage,
        st.session_state.get("first_reflection"),
        st.session_state.get("self_reflection"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()

def reset_journey():
    cursor.execute(
        "DELETE FROM progress WHERE user_email = ?",
        (st.session_state.user_email,)
    )
    conn.commit()

    for k in ["stage", "first_reflection", "self_reflection"]:
        if k in st.session_state:
            del st.session_state[k]

    st.session_state.stage = "landing"
    st.rerun()

# -----------------------------
# APP FLOW
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
