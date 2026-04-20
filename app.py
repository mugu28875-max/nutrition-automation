import streamlit as st
import pdfplumber
import pandas as pd
import re

st.title("📄 Nutrition PDF → Illustrator CSV Converter")

uploaded_file = st.file_uploader("Upload Nutrition PDF", type="pdf")


def clean_key(text):
    text = re.sub(r'[^a-zA-Z0-9]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def extract_data(text):
    data = []
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # ENERGY (2-line)
        if line.startswith("Energy"):
            kj_match = re.search(r"Energy\s+([\d\.]+)\s*kJ\s+([\d\.]+)\s*kJ\s+\((\d+%)\)", line)

            if i + 1 < len(lines):
                next_line = lines[i + 1]
                kcal_match = re.search(r"([\d\.]+)\s*kcal\s+([\d\.]+)\s*kcal", next_line)
            else:
                kcal_match = None

            if kj_match:
                data.append([
                    "Energy_kJ",
                    kj_match.group(1) + " kJ",
                    kj_match.group(2) + " kJ",
                    kj_match.group(3)
                ])

            if kcal_match:
                data.append([
                    "Energy_kcal",
                    kcal_match.group(1) + " kcal",
                    kcal_match.group(2) + " kcal",
                    "0%"
                ])

            i += 2
            continue

        # Other nutrients
        elif any(x in line for x in ["Fat", "saturates", "Carbohydrate", "sugars", "Protein", "Salt"]):
            match = re.search(r"([\d\.]+\s*g)\s+([\d\.]+\s*g)\s+\((\d+%)\)", line)

            if match:
                if "Fat" in line:
                    name = "Fat"
                elif "saturates" in line:
                    name = "Saturates"
                elif "Carbohydrate" in line:
                    name = "Carbohydrate"
                elif "sugars" in line:
                    name = "Sugars"
                elif "Protein" in line:
                    name = "Protein"
                elif "Salt" in line:
                    name = "Salt"

                data.append([name, match.group(1), match.group(2), match.group(3)])

        i += 1

    return data


if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        text = pdf.pages[0].extract_text()

    st.subheader("Extracted Text")
    st.text(text)

    data = extract_data(text)

    # Flatten to Illustrator format
    flat_data = {"Name": "Label1"}

    for row in data:
        nutrient = clean_key(row[0])

        flat_data[f"{nutrient}_100ml"] = row[1]
        flat_data[f"{nutrient}_250ml"] = row[2]
        flat_data[f"{nutrient}_Percent"] = row[3]

    df = pd.DataFrame([flat_data])

    st.subheader("Preview Table")
    st.dataframe(df)

    # Save CSV (Desktop path – change if needed)
    csv_path = "nutrition_ai_ready.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")

    st.success("✅ CSV saved to Desktop")

    with open(csv_path, "rb") as f:
        st.download_button("⬇ Download CSV", f, file_name="nutrition_ai_ready.csv")