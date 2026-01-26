import streamlit as st

# Page config
st.set_page_config(page_title="WHY", layout="centered")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "landing"

# LANDING PAGE
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

    user_input = st.text_area("Take your time. Write honestly.", height=150)

    if st.button("Continue"):
        if user_input.strip() != "":
            st.session_state.first_reflection = user_input
            st.session_state.stage = "reflection"
            st.rerun()
        else:
            st.warning("You can write even one word.")

# REFLECTION RESPONSE
elif st.session_state.stage == "reflection":
    st.subheader("Reflection")

    st.write(
        "That question matters.\n\n"
        "You don’t need to solve it right now. "
        "Just noticing it is enough for today."
    )

    st.write("You wrote:")
    st.info(st.session_state.first_reflection)

    st.write("We’ll continue from here next time.")
