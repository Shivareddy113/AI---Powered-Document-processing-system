import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO
from datetime import datetime

# PDF Report
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="AI Document Processing System", layout="wide")
st.title("📄 AI-Powered Document Processing System")


# ========================
# Helper: PDF Generator
# ========================
def generate_pdf_report(result):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Logo (your picture from Desktop)
    try:
        logo_path = r"C:\Users\shiva\OneDrive\Desktop\desk.jpg"  # <-- Replace 'your_logo.png' with your actual file name
        logo = Image(logo_path, width=100, height=50)
        elements.append(logo)
    except:
        elements.append(Paragraph("<b>[Logo not found]</b>", styles["Normal"]))

    # Title
    elements.append(Paragraph(
        "<b><font size=18 color='blue'>AI Document Processing Report</font></b>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 12))

    # Summary
    total_entities = len(result.get("entities", []))
    valid_count = sum([1 for v in result.get("validated", []) if v.get("valid") is True])
    invalid_count = sum([1 for v in result.get("validated", []) if v.get("valid") is False])

    summary_data = [
        ["📑 Total Entities", "✅ Valid Entities", "❌ Invalid Entities"],
        [str(total_entities), str(valid_count), str(invalid_count)]
    ]
    summary_table = Table(summary_data, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Entities
    entities = result.get("entities", [])
    if entities:
        entity_data = [["Entity", "Type"]] + [[e.get("text", ""), e.get("label", "")] for e in entities]
        entity_table = Table(entity_data, hAlign="LEFT")
        entity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))
        elements.append(Paragraph("<b>📑 Extracted Entities</b>", styles["Heading2"]))
        elements.append(entity_table)
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph("⚠️ No entities extracted.", styles["Normal"]))

    # Validation
    validations = result.get("validated", [])
    if validations:
        validation_data = [["Entity", "Valid", "Reason"]] + [
            [v.get("entity", ""), "✅" if v.get("valid") else "❌", v.get("reason", "")]
            for v in validations
        ]
        validation_table = Table(validation_data, hAlign="LEFT")
        validation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))
        elements.append(Paragraph("<b>✅ Validation Results</b>", styles["Heading2"]))
        elements.append(validation_table)
    else:
        elements.append(Paragraph("⚠️ No validation results available.", styles["Normal"]))

    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ========================
# Helper: Show Results + Download
# ========================
def show_results(result):
    if result["entities"]:
        df_entities = pd.DataFrame(result["entities"])
        df_valid = pd.DataFrame(result["validated"])

        # Summary metrics
        total_entities = len(df_entities)
        valid_count = df_valid["valid"].sum(skipna=True) if "valid" in df_valid else 0
        invalid_count = total_entities - valid_count

        col1, col2, col3 = st.columns(3)
        col1.metric("📑 Total Entities", total_entities)
        col2.metric("✅ Valid Entities", valid_count)
        col3.metric("❌ Invalid Entities", invalid_count)

        # Entities Table
        st.subheader("📑 Extracted Entities")
        st.table(df_entities)

        # Validation Table
        st.subheader("✅ Validation Results")
        st.table(df_valid)

        # Download Buttons
        st.subheader("⬇️ Download Results")

        filename = result.get("filename", f"doc_{datetime.now().strftime('%H%M%S')}")

        json_data = json.dumps(result, indent=4)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"{filename}_results.json",
            mime="application/json",
            key=f"json_download_{filename}"
        )

        csv_data = df_valid.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Validation as CSV",
            data=csv_data,
            file_name=f"{filename}_validation.csv",
            mime="text/csv",
            key=f"csv_download_{filename}"
        )

        pdf_buffer = generate_pdf_report(result)
        st.download_button(
            label="📥 Download Full Report (PDF)",
            data=pdf_buffer,
            file_name=f"{filename}_report.pdf",
            mime="application/pdf",
            key=f"pdf_download_{filename}"
        )

    else:
        st.info("No entities extracted")


# ========================
# 1️⃣ Upload and Process New Document
# ========================
st.header("📤 Upload and Process Document")

uploaded_file = st.file_uploader("Upload a document", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    files = {"file": open(uploaded_file.name, "rb")}
    response = requests.post(f"{API_URL}/process-document/", files=files)

    if response.status_code == 200:
        result = response.json()
        st.success("✅ Document processed successfully!")
        show_results(result)
    else:
        st.error("❌ Failed to process document")


# ========================
# 2️⃣ View Already Processed Documents
# ========================
st.header("📂 View Processed Documents")

docs_response = requests.get(f"{API_URL}/processed-documents/")
if docs_response.status_code == 200:
    files = docs_response.json().get("processed_files", [])
    if files:
        selected_file = st.selectbox("Select a processed document", files)
        if st.button("View Document Results"):
            doc_response = requests.get(f"{API_URL}/processed-documents/{selected_file}")
            if doc_response.status_code == 200:
                doc_result = doc_response.json()
                show_results(doc_result)
            else:
                st.error("❌ Could not fetch document results")
    else:
        st.info("No processed documents found yet.")
else:
    st.error("❌ Failed to load processed documents")
