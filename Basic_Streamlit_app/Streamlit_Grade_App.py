import streamlit as st

st.title("Mark to Grade Converter")

mark = st.number_input(
    "Enter your mark (0 - 100):",
    min_value=0,
    max_value=100,
    value=0,
    step=1
)

if st.button("Calculate Grade"):

    if mark >= 90:
        grade = "A"
    elif mark >= 80:
        grade = "B"
    elif mark >= 70:
        grade = "C"
    elif mark >= 60:
        grade = "D"
    else:
        grade = "E"

    st.success(f"Your grade is: {grade}")