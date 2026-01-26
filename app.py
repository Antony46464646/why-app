import streamlit as st

# Page config
st.set_page_config(page_title="WHY", layout="centered")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "landing"

# LANDING
if st.session_state.stage == "landing":
    st.title("WHY")
    st.write("The universe has questions. So do you.")

    if st.button("Begin"):
        st.session_state.stage = "arrival"
        st.rerun()

# STAGE 1 — ARRIVAL
elif st.session_state.stage == "arrival":
    st.subheader("Stage 1 · Arrival")
    st.write("What question or feeling brought you here today?")
    st.write("Take your time. Write honestly.")

    user_input = st.text_area("", height=150)

    if st.button("Continue"):
        if user_input.strip():
            st.session_state.first_reflection = user_input
            st.session_state.stage = "reflection"
            st.rerun()
        else:
            st.warning("Even one word is enough.")

# REFLECTION
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
        st.rerun()

# STAGE 2 — SELF
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
            st.rerun()
        else:
            st.warning("There is no wrong answer.")

# PAUSE
elif st.session_state.stage == "pause":
    st.subheader("Pause")

    st.write(
        "You’ve gone far enough for now.\n\n"
        "We don’t need to rush meaning.\n"
        "We’ll continue from here next time."
    )
