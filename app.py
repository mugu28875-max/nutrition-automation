import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

st.title("📄 Nutrition PDF → Illustrator CSV Converter")

uploaded_file = st.file_uploader("Upload Nutrition PDF", type="pdf")


def clean_key(text):
    text = re.sub(r'[^a-zA-Z0-9]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


# -------------------------
# 🔍 ENGLISH PARSER
# -------------------------
def extract_english(text):
    data = []

    text = text.replace(",", ".")
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # ENERGY (multi-line safe)
        if "Energy" in line:
            combined = line

            if i + 1 < len(lines):
                combined += " " + lines[i + 1]
            if i + 2 < len(lines):
                combined += " " + lines[i + 2]

            nums = re.findall(r"[\d]+\.?[\d]*", combined)

            if len(nums) >= 5:
                data.append(["Energy_kJ", nums[0] + " kJ", nums[2] + " kJ", nums[4] + "%"])
                data.append(["Energy_kcal", nums[1] + " kcal", nums[3] + " kcal", "0%"])

            i += 3
            continue

        # OTHER NUTRIENTS
        elif any(x in line for x in ["Fat:", "saturates:", "Carbohydrate:", "sugars:", "Protein:", "Salt:"]):

            match = re.search(r"([\d\.]+\s*g)\s+([\d\.]+\s*g)\s+\((\d+%)\)", line)

            if match:
                if "Fat:" in line:
                    name = "Fat"
                elif "saturates:" in line:
                    name = "Saturates"
                elif "Carbohydrate:" in line:
                    name = "Carbohydrate"
                elif "sugars:" in line:
                    name = "Sugars"
                elif "Protein:" in line:
                    name = "Protein"
                elif "Salt:" in line:
                    name = "Salt"

                data.append([name, match.group(1), match.group(2), match.group(3)])

        i += 1

    return data


# -------------------------
# 🔍 HUNGARIAN PARSER
# -------------------------
def extract_hungarian(text):
    data = []

    text = text.replace(",", ".")
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # ENERGY (multi-line safe)
        if "Energia" in line:
            combined = line

            if i + 1 < len(lines):
                combined += " " + lines[i + 1]
            if i + 2 < len(lines):
                combined += " " + lines[i + 2]

            nums = re.findall(r"[\d]+\.?[\d]*", combined)

            if len(nums) >= 5:
                data.append(["Energia_kJ", nums[0] + " kJ", nums[2] + " kJ", nums[4] + "%"])
                data.append(["Energia_kcal", nums[1] + " kcal", nums[3] + " kcal", "0%"])

            i += 3
            continue

        # OTHER NUTRIENTS
        else:
            for hu_key in ["Zsír", "telített", "Szénhidrát", "cukrok", "Fehérje", "Só"]:

                if hu_key in line:
                    match = re.search(r"([\d\.]+\s*g)\s+([\d\.]+\s*g)\s+\((\d+%)\)", line)

                    if match:
                        if hu_key == "Zsír":
                            name = "Zsír"
                        elif hu_key == "telített":
                            name = "Telített_zsír"
                        elif hu_key == "Szénhidrát":
                            name = "Szénhidrát"
                        elif hu_key == "cukrok":
                            name = "Cukrok"
                        elif hu_key == "Fehérje":
                            name = "Fehérje"
                        elif hu_key == "Só":
                            name = "Só"

                        data.append([name, match.group(1), match.group(2), match.group(3)])

        i += 1

    return data


# -------------------------
# 🚀 MAIN APP
# -------------------------
if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        text = pdf.pages[0].extract_text() or ""

    st.subheader("📄 Extracted Text")
    st.text(text)

    # Extract both languages
    data_en = extract_english(text)
    data_hu = extract_hungarian(text)

    # -------------------------
    # 🔍 Visual Tables
    # -------------------------
    st.subheader("🔍 English Table")
    df_en = pd.DataFrame(data_en, columns=["Nutrient", "100ml", "250ml", "%"])
    st.dataframe(df_en)

    st.subheader("🔍 Hungarian Table")
    df_hu = pd.DataFrame(data_hu, columns=["Tápanyag", "100ml", "250ml", "%"])
    st.dataframe(df_hu)

    # -------------------------
    # 📦 Illustrator Export (EN only)
    # -------------------------
    flat_data = {"Name": "Label1"}

    for row in data_en:
        nutrient = clean_key(row[0])
        flat_data[f"{nutrient}_100ml"] = row[1]
        flat_data[f"{nutrient}_250ml"] = row[2]
        flat_data[f"{nutrient}_Percent"] = row[3]

    df_export = pd.DataFrame([flat_data])

    st.subheader("📦 Illustrator Table (Export)")
    st.dataframe(df_export)

    # -------------------------
    # ⬇ Download CSV
    # -------------------------
    csv_buffer = io.StringIO()
    df_export.to_csv(csv_buffer, index=False)

    st.download_button(
        label="⬇ Download Illustrator CSV",
        data=csv_buffer.getvalue(),
        file_name="nutrition_ai_ready.csv",
        mime="text/csv"
    )