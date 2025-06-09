import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import math
import io

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪚 Quartz Slab Layout Optimizer")

uploaded_file = st.file_uploader("Upload CSV file with part data", type=["csv"])

# User-defined inputs
slab_length_in = st.number_input("Slab Length (inches)", min_value=10.0, value=127.0, step=1.0)
slab_width_in = st.number_input("Slab Width (inches)", min_value=10.0, value=64.0, step=1.0)
gap = st.number_input("Cutting gap between parts (in inches)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=lambda x: x.strip())

    # Convert ft to inches and replicate parts by quantity
    parts = []
    for _, row in df.iterrows():
        for _ in range(int(row['Quantity'])):
            part = {
                'label': row['Label'],
                'width': float(row['Width (ft)']) * 12 + gap,
                'height': float(row['Length (ft)']) * 12 + gap
            }
            parts.append(part)

    # Sort parts by area (descending)
    parts.sort(key=lambda x: x['width'] * x['height'], reverse=True)

    # Simple greedy placement algorithm
    slabs = []
    for part in parts:
        placed = False
        for slab in slabs:
            for y in range(0, int(slab_length_in - part['height'] + 1), int(gap) + 1):
                for x in range(0, int(slab_width_in - part['width'] + 1), int(gap) + 1):
                    fits = True
                    for other in slab['parts']:
                        if not (
                            x + part['width'] <= other['x'] or
                            x >= other['x'] + other['width'] or
                            y + part['height'] <= other['y'] or
                            y >= other['y'] + other['height']
                        ):
                            fits = False
                            break
                    if fits:
                        slab['parts'].append({**part, 'x': x, 'y': y})
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            slabs.append({'parts': [{**part, 'x': 0, 'y': 0}]})

    st.success(f"Optimized into {len(slabs)} slabs.")

    # Draw all slabs to PDF
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for i, slab in enumerate(slabs):
            if i % 6 == 0:
                fig, axs = plt.subplots(3, 2, figsize=(36, 24))
                axs = axs.flatten()
            ax = axs[i % 6]
            ax.set_xlim(0, slab_width_in)
            ax.set_ylim(0, slab_length_in)
            ax.set_title(f"Slab {i + 1}")
            ax.set_aspect('equal')
            for part in slab['parts']:
                rect = plt.Rectangle((part['x'], part['y']), part['width'], part['height'], fill=None, edgecolor='blue', linewidth=1.5)
                ax.add_patch(rect)
                ax.text(part['x'] + part['width']/2, part['y'] + part['height']/2, part['label'], fontsize=10, ha='center', va='center')
            ax.invert_yaxis()
            if (i + 1) % 6 == 0 or (i + 1) == len(slabs):
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()

    st.download_button(
        label="📄 Download Slab Layout PDF",
        data=pdf_buffer.getvalue(),
        file_name="slab_layout.pdf",
        mime="application/pdf"
    )

    st.write("\n📌 Sample Input Format:")
    st.code("""Label,Length (ft),Width (ft),Quantity
island top,7,3.5,8
island side,3,3.5,16
kitchen 1,2.75,2,8
kitchen 2,5.5,2,8
bath 1,9.1,1.75,8
bath 2,2,1.75,8""")
