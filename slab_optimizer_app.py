import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import math
import io

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪚 Quartz Slab Cutting Layout Optimizer")

# Step 1: Slab dimensions and gap
st.subheader("Step 1: Define Slab Dimensions and Cutting Gap")
slab_length_in = st.number_input("Enter Slab Length (inches)", min_value=10.0, value=127.0, step=1.0)
slab_width_in = st.number_input("Enter Slab Width (inches)", min_value=10.0, value=64.0, step=1.0)
gap = st.number_input("Enter Blade Cutting Gap (in inches)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

# Step 2: Manual or CSV input
st.subheader("Step 2: Provide Countertop Info")
tab1, tab2 = st.tabs(["📝 Enter Manually", "📁 Upload CSV File"])

df = None

with tab1:
    manual_data = []
    with st.form("manual_input_form"):
        for i in range(8):
            col1, col2, col3, col4 = st.columns(4)
            label = col1.text_input(f"Label {i+1}", key=f"label_{i}")
            length = col2.number_input(f"Length (ft) {i+1}", min_value=0.0, step=0.1, key=f"len_{i}")
            width = col3.number_input(f"Width (ft) {i+1}", min_value=0.0, step=0.1, key=f"wid_{i}")
            quantity = col4.number_input(f"Qty {i+1}", min_value=0, step=1, key=f"qty_{i}")
            if label and length > 0 and width > 0 and quantity > 0:
                manual_data.append({"Label": label, "Length (ft)": length, "Width (ft)": width, "Quantity": quantity})
        submitted = st.form_submit_button("Submit Manual Entries")
        if submitted:
            df = pd.DataFrame(manual_data)

with tab2:
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    st.markdown("""
    ##### 📌 Sample CSV Format
    ```csv
    Label,Length (ft),Width (ft),Quantity
    island top,7,3.5,8
    island side,3,3.5,16
    kitchen 1,2.75,2,8
    kitchen 2,5.5,2,8
    bath 1,9.1,1.75,8
    bath 2,2,1.75,8
    ```
    """)
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df = df.rename(columns=lambda x: x.strip())

if df is not None and not df.empty:
    # Prepare parts list (converted to inches)
    parts = []
    for _, row in df.iterrows():
        for _ in range(int(row['Quantity'])):
            part = {
                'label': row['Label'],
                'width': float(row['Width (ft)']) * 12 + gap,
                'height': float(row['Length (ft)']) * 12 + gap
            }
            parts.append(part)

    # Sort by max dimension (to improve fit)
    parts.sort(key=lambda x: max(x['width'], x['height']), reverse=True)

    # Place parts using simple shelf packing with rotation
    slabs = []
    for part in parts:
        placed = False
        for slab in slabs:
            for shelf in slab['shelves']:
                for orientation in [(part['width'], part['height']), (part['height'], part['width'])]:
                    w, h = orientation
                    if shelf['x'] + w <= slab_width_in and shelf['y'] + h <= slab_length_in:
                        part_coords = {**part, 'x': shelf['x'], 'y': shelf['y'], 'width': w, 'height': h}
                        shelf['parts'].append(part_coords)
                        shelf['x'] += w + gap
                        slab['parts'].append(part_coords)
                        placed = True
                        break
                if placed:
                    break
            if not placed and slab['shelves'][-1]['y'] + part['height'] + gap <= slab_length_in:
                shelf = {'x': 0, 'y': slab['shelves'][-1]['y'] + max(p['height'] for p in slab['shelves'][-1]['parts']) + gap, 'parts': []}
                slab['shelves'].append(shelf)
        if not placed:
            new_slab = {'parts': [], 'shelves': [{'x': 0, 'y': 0, 'parts': []}]}
            slabs.append(new_slab)
            new_slab['shelves'][0]['parts'].append({**part, 'x': 0, 'y': 0})
            new_slab['parts'].append({**part, 'x': 0, 'y': 0})
            new_slab['shelves'][0]['x'] += part['width'] + gap

    st.success(f"You will need {len(slabs)} slabs")

    # Create PDF with slab diagrams
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for i in range(0, len(slabs), 6):
            fig, axs = plt.subplots(3, 2, figsize=(36, 24))
            axs = axs.flatten()
            for j in range(min(6, len(slabs) - i)):
                slab = slabs[i + j]
                ax = axs[j]
                ax.set_xlim(0, slab_length_in)
                ax.set_ylim(0, slab_width_in)
                ax.set_title(f"Slab {i + j + 1}")
                ax.set_aspect('equal')
                for part in slab['parts']:
                    rect = plt.Rectangle((part['y'], part['x']), part['height'], part['width'], facecolor='skyblue', edgecolor='blue', linewidth=1.5)
                    ax.add_patch(rect)
                    ax.text(part['y'] + part['height']/2, part['x'] + part['width']/2, part['label'], fontsize=10, ha='center', va='center')
                ax.invert_yaxis()
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()

    st.download_button(
        label="📄 Download Slab Layout PDF",
        data=pdf_buffer.getvalue(),
        file_name="slab_layout.pdf",
        mime="application/pdf"
    )
