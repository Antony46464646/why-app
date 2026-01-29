import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import secrets

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
CREATE TABLE IF NOT EXISTS login_tokens (
    token TEXT PRIMARY KEY,
    user_email TEXT,
    created_at TEXT
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS journey_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    stage1 TEXT,
    stage2 TEXT,
    saved_at TEXT
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

def create_login_token(email):
    token = secrets.token_urlsafe(32)
    cursor.execute(
        "INSERT INTO login_tokens VALUES (?, ?, ?)",
        (token, email, datetime.utcnow().isoformat())
    )
    conn.commit()
    st.experimental_set_query_params(token=token)

def get_user_from_token():
    params = st.experimental_get_query_params()
    token = params.get("token", [None])[0]
    if not token:
        return None
    cursor.execute(
        "SELECT user_email FROM login_tokens WHERE token = ?",
        (token,)
    )
    row = cursor.fetchone()
    return row[0] if row else None

def clear_login_token():
    params = st.experimental_get_query_params()
    token = params.get("token", [None])[0]
    if token:
        cursor.execute("DELETE FROM login_tokens WHERE token = ?", (token,))
        conn.commit()
    st.experimental_set_query_params()

# -----------------------------
# JOURNEY HELPERS
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

def archive_current_journey():
    cursor.execute("""
        INSERT INTO journey_history (user_email, stage1, stage2, saved_at)
        VALUES (?, ?, ?, ?)
    """, (
        st.session_state.user_email,
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
        st.session_state.pop(k, None)
    st.session_state.stage = "landing"
    st.rerun()

# -----------------------------
# SESSION BOOTSTRAP
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = get_user_from_token()

if "view_history" not in st.session_state:
    st.session_state.view_history = False

# -----------------------------
# LOGIN / REGISTER
# -----------------------------
if not st.session_state.user_email:
    st.title("WHY")
    st.caption("This space is private. Nothing is shared.")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(email, password):
            create_login_token(email)
            st.session_state.user_email = email
            st.session_state.pop("stage", None)
            st.success("Login successful")
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
    clear_login_token()
    st.session_state.clear()
    st.rerun()

# -----------------------------
# ENTRY / RESTORE
# -----------------------------
if "stage" not in st.session_state:
    load_user_progress(st.session_state.user_email)

# -----------------------------
# HISTORY VIEW
# -----------------------------
if st.session_state.view_history:
    st.title("Past journeys")

    cursor.execute("""
        SELECT stage1, stage2, saved_at
        FROM journey_history
        WHERE user_email = ?
        ORDER BY saved_at DESC
    """, (st.session_state.user_email,))
    rows = cursor.fetchall()

    if not rows:
        st.info("No past journeys yet.")
    else:
        for stage1, stage2, saved_at in rows:
            st.markdown(f"**Saved on:** {saved_at[:10]}")
            st.write(stage1)
            st.write(stage2)
            st.divider()

    if st.button("Back"):
        st.session_state.view_history = False
        st.rerun()

    st.stop()

# -----------------------------
# APP FLOW
# -----------------------------
if st.session_state.stage == "landing":
    st.title("WHY")
    st.write("The universe has questions.")
    st.write("You don’t need answers today.")

    if st.button("Begin gently"):
        st.session_state.stage = "arrival"
        save_progress()
        st.rerun()

    if st.button("View past journeys"):
        st.session_state.view_history = True
        st.rerun()

elif st.session_state.stage == "arrival":
    st.subheader("Arrival")
    st.caption("There’s no right way to answer. Even a few words are enough.")

    user_input = st.text_area("", height=150)

    if st.button("Continue when ready"):
        if user_input.strip():
            st.session_state.first_reflection = user_input
            st.session_state.stage = "reflection"
            save_progress()
            st.rerun()

elif st.session_state.stage == "reflection":
    st.subheader("Reflection")
    st.info(st.session_state.first_reflection)

    if st.button("Go a little deeper"):
        st.session_state.stage = "self"
        save_progress()
        st.rerun()

elif st.session_state.stage == "self":
    st.subheader("Self")
    self_input = st.text_area("", height=150)

    if st.button("Continue when ready"):
        if self_input.strip():
            st.session_state.self_reflection = self_input
            st.session_state.stage = "pause"
            save_progress()
            st.rerun()

elif st.session_state.stage == "pause":
    st.subheader("Pause")
    st.write("You’ve gone far enough for now.")
    st.write("Nothing needs to be solved. We’ll continue when you return.")

    archive_current_journey()

    if st.button("Start a new journey"):
        reset_journey()
