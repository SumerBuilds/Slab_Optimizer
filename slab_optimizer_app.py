import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io
from rectpack import newPacker

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪚 Quartz Slab Cutting Layout Optimizer (Powered by MaxRects)")

# Input slab dimensions and kerf
tab1, tab2 = st.tabs(["📝 Enter Manually", "📁 Upload CSV File"])

slab_length_in = st.number_input("Enter Slab Length (inches)", min_value=10.0, value=127.0)
slab_width_in = st.number_input("Enter Slab Width (inches)", min_value=10.0, value=64.0)
gap = st.number_input("Enter Blade Cutting Gap (in inches)", min_value=0.0, value=0.5, step=0.1)

# Load data
df = None
with tab1:
    manual_data = []
    with st.form("manual_input"):
        for i in range(8):
            cols = st.columns(4)
            label = cols[0].text_input(f"Label {i+1}", key=f"label_{i}")
            length = cols[1].number_input(f"Length (ft) {i+1}", min_value=0.0, step=0.1, key=f"len_{i}")
            width = cols[2].number_input(f"Width (ft) {i+1}", min_value=0.0, step=0.1, key=f"wid_{i}")
            qty = cols[3].number_input(f"Qty {i+1}", min_value=0, step=1, key=f"qty_{i}")
            if label and length > 0 and width > 0 and qty > 0:
                manual_data.append({"Label": label, "Length (ft)": length, "Width (ft)": width, "Quantity": qty})
        submitted = st.form_submit_button("Submit")
        if submitted:
            df = pd.DataFrame(manual_data)

with tab2:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    st.markdown("""### Example Format:
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
    if uploaded:
        df = pd.read_csv(uploaded)

if df is not None:
    pieces = []
    labels = []
    for _, row in df.iterrows():
        label = row['Label']
        length = float(row['Length (ft)']) * 12 + gap
        width = float(row['Width (ft)']) * 12 + gap
        qty = int(row['Quantity'])
        for _ in range(qty):
            pieces.append((width, length))  # rectpack uses (width, height)
            labels.append(label)

    # Start packing
    packer = newPacker(rotation=True)
    rect_data = [(w, h, i) for i, (w, h) in enumerate(pieces)]

    for r in rect_data:
        packer.add_rect(*r)
    for _ in range(len(pieces)):
        packer.add_bin(slab_width_in, slab_length_in)

    packer.pack()

    bins = packer.bin_rects()
    st.success(f"You will need {len(bins)} slabs")

    # Draw PDF
    pdf_bytes = io.BytesIO()
    with PdfPages(pdf_bytes) as pdf:
        for idx, b in enumerate(bins):
            fig, ax = plt.subplots(figsize=(36, 24))
            ax.set_xlim(0, slab_length_in)
            ax.set_ylim(0, slab_width_in)
            ax.set_aspect('equal')
            ax.set_title(f"Slab {idx + 1}")
            for x, y, w, h, rid in b:
                label = labels[rid]
                rect = plt.Rectangle((y, x), h, w, facecolor='skyblue', edgecolor='blue')
                ax.add_patch(rect)
                ax.text(y + h/2, x + w/2, label, ha='center', va='center', fontsize=10)
            ax.invert_yaxis()
            pdf.savefig(fig)
            plt.close()

    st.download_button("📄 Download Slab Layout PDF", data=pdf_bytes.getvalue(), file_name="slab_layout_optimized.pdf", mime="application/pdf")
