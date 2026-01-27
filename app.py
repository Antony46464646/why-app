import streamlit as st
import sqlite3
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="WHY", layout="centered")

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("progress.db", check_same_thread=False)
cursor = conn.cursor()

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
# SESSION ID
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(id(st.session_state))

# -----------------------------
# LOAD SAVED PROGRESS
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
# SAVE FUNCTION
# -----------------------------
def save_progress():
    cursor.execute("""
        INSERT OR REPLACE INTO progress
        (session_id, stage, stage1, stage2, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.session_id,
        st.session_state.stage,
        st.session_state.get("first_reflection"),
        st.session_state.get("self_reflection"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()

# -----------------------------
# RESET FUNCTION (NEW)
# -----------------------------
def reset_journey():
    cursor.execute(
        "DELETE FROM progress WHERE session_id = ?",
        (st.session_state.session_id,)
    )
    conn.commit()

    for key in ["stage", "first_reflection", "self_reflection"]:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.stage = "landing"
    st.rerun()

# -----------------------------
# LANDING
# -----------------------------
if st.session_state.stage == "landing":
    st.title("WHY")
    st.write("The universe has questions. So do you.")

    if st.button("Begin"):
        st.session_state.stage = "arrival"
        save_progress()
        st.rerun()

# -----------------------------
# STAGE 1 — ARRIVAL
# -----------------------------
elif st.session_state.stage == "arrival":
    st.subheader("Stage 1 · Arrival")
    st.write("What question or feeling brought you here today?")
    st.write("Take your time. Write honestly.")

    user_input = st.text_area("", height=150)

    if st.button("Continue"):
        if user_input.strip():
            st.session_state.first_reflection = user_input
            st.session_state.stage = "reflection"
            save_progress()
            st.rerun()
        else:
            st.warning("Even one word is enough.")

# -----------------------------
# REFLECTION
# -----------------------------
elif st.session_state.stage == "reflection":
    st.subheader("Reflection")

    st.write("That question matters.")
    st.write(
        "You don’t need to solve it right now. "
        "Just noticing it is enough for today."
    )

    st.write("You wrote:")
    st.info(st.session_state.first_reflection)

    if st.button("Continue deeper"):
        st.session_state.stage = "self"
        save_progress()
        st.rerun()

# -----------------------------
# STAGE 2 — SELF
# -----------------------------
elif st.session_state.stage == "self":
    st.subheader("Stage 2 · Self")

    st.write(
        "When you sit with this feeling,\n"
        "what feels most present right now?"
    )

    self_input = st.text_area("Write whatever comes.", height=150)

    if st.button("Continue"):
        if self_input.strip():
            st.session_state.self_reflection = self_input
            st.session_state.stage = "pause"
            save_progress()
            st.rerun()
        else:
            st.warning("There is no wrong answer.")

# -----------------------------
# PAUSE
# -----------------------------
elif st.session_state.stage == "pause":
    st.subheader("Pause")

    st.write(
        "You’ve gone far enough for now.\n\n"
        "We don’t need to rush meaning.\n"
        "We’ll continue from here next time."
    )

    save_progress()

    st.divider()

    if st.button("Start a new journey"):
        reset_journey()
