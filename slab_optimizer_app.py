import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import math
import io

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪚 Quartz Slab Cutting Layout Optimizer")

# User-defined slab dimensions and cutting gap
st.subheader("Step 1: Define Slab Dimensions and Cutting Gap")
slab_length_in = st.number_input("Enter Slab Length (inches)", min_value=10.0, value=127.0, step=1.0)
slab_width_in = st.number_input("Enter Slab Width (inches)", min_value=10.0, value=64.0, step=1.0)
gap = st.number_input("Enter Blade Cutting Gap (in inches)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

# Upload CSV file or enter manually
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

    # Sample input format
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
    parts = []
    for _, row in df.iterrows():
        for _ in range(int(row['Quantity'])):
            length_in = float(row['Length (ft)']) * 12
            width_in = float(row['Width (ft)']) * 12
            parts.append({
                'label': row['Label'],
                'width': width_in,
                'height': length_in
            })

    # Sort parts by perimeter (descending)
    parts.sort(key=lambda x: 2 * (x['width'] + x['height']), reverse=True)

    def fits(part, rect):
        # Try placing with and without rotation
        if part['width'] + gap <= rect['width'] and part['height'] + gap <= rect['height']:
            return part['width'], part['height']
        elif part['height'] + gap <= rect['width'] and part['width'] + gap <= rect['height']:
            return part['height'], part['width']
        return None

    def pack_parts(parts, slab_width, slab_height):
        slabs = []
        for part in parts:
            placed = False
            for slab in slabs:
                for i, free in enumerate(slab['free_rects']):
                    fit = fits(part, free)
                    if fit:
                        pw, ph = fit
                        px, py = free['x'], free['y']
                        slab['parts'].append({**part, 'x': px, 'y': py, 'width': pw, 'height': ph})

                        # Create new rects
                        new_rects = [
                            {'x': px + pw + gap, 'y': py, 'width': free['width'] - pw - gap, 'height': ph},
                            {'x': px, 'y': py + ph + gap, 'width': free['width'], 'height': free['height'] - ph - gap},
                        ]
                        slab['free_rects'].pop(i)
                        for rect in new_rects:
                            if rect['width'] > 0 and rect['height'] > 0:
                                slab['free_rects'].append(rect)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                new_slab = {
                    'parts': [],
                    'free_rects': [{'x': 0, 'y': 0, 'width': slab_width, 'height': slab_height}]
                }
                fit = fits(part, new_slab['free_rects'][0])
                if fit:
                    pw, ph = fit
                    px, py = 0, 0
                    new_slab['parts'].append({**part, 'x': px, 'y': py, 'width': pw, 'height': ph})
                    new_slab['free_rects'] = [
                        {'x': px + pw + gap, 'y': py, 'width': slab_width - pw - gap, 'height': ph},
                        {'x': px, 'y': py + ph + gap, 'width': slab_width, 'height': slab_height - ph - gap},
                    ]
                slabs.append(new_slab)
        return slabs

    slabs = pack_parts(parts, slab_length_in, slab_width_in)

    st.success(f"You will need {len(slabs)} slabs")

    # Draw slabs to PDF
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for i, slab in enumerate(slabs):
            if i % 6 == 0:
                fig, axs = plt.subplots(3, 2, figsize=(36, 24))
                axs = axs.flatten()
            ax = axs[i % 6]
            ax.set_xlim(0, slab_length_in)
            ax.set_ylim(0, slab_width_in)
            ax.set_title(f"Slab {i + 1}")
            ax.set_aspect('equal')
            for part in slab['parts']:
                rect = plt.Rectangle((part['x'], part['y']), part['width'], part['height'], facecolor='skyblue', edgecolor='blue', linewidth=1.5)
                ax.add_patch(rect)
                ax.text(part['x'] + part['width']/2, part['y'] + part['height']/2, part['label'], fontsize=10, ha='center', va='center')
            ax.invert_yaxis()
            if (i % 6 == 5) or (i == len(slabs) - 1):
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()

    st.download_button(
        label="📄 Download Slab Layout PDF",
        data=pdf_buffer.getvalue(),
        file_name="slab_layout.pdf",
        mime="application/pdf"
    )
