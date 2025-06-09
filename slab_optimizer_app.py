import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io
from rectpack import newPacker

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪚 Quartz Slab Cutting Layout Optimizer")

# Input slab dimensions and kerf
slab_length_in = st.number_input("Enter Slab Length (inches)", min_value=10.0, value=127.0)
slab_width_in = st.number_input("Enter Slab Width (inches)", min_value=10.0, value=64.0)
gap = st.number_input("Enter Blade Cutting Gap (in inches)", min_value=0.0, value=0.5, step=0.1)

# Load data
tab1, tab2 = st.tabs(["📝 Enter Manually", "📁 Upload CSV File"])
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
    sample_csv = """Label,Length (ft),Width (ft),Quantity
island top,7,3.5,8
island side,3,3.5,16
kitchen 1,2.75,2,8
kitchen 2,5.5,2,8
bath 1,9.1,1.75,8
bath 2,2,1.75,8
"""
    st.download_button(
        label="📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_countertops.csv",
        mime="text/csv"
    )
    
    if uploaded:
        df = pd.read_csv(uploaded)

if df is not None:
    grouped = df.groupby("Label")
    pieces = []
    label_lookup = {}
    total_countertop_area = 0
    rect_id = 0

    for label, rows in grouped:
        row = rows.iloc[0]
        l_in = float(row['Length (ft)']) * 12
        w_in = float(row['Width (ft)']) * 12
        qty = int(row['Quantity'])
        total_countertop_area += l_in * w_in * qty
        for _ in range(qty):
            pieces.append((w_in, l_in, rect_id, label))
            label_lookup[rect_id] = label
            rect_id += 1

    # Custom geometry-based slab packing
    MIN_GAP = gap  # inches (user-defined)

def can_place_with_gap(piece, placed, slab_size):
    px, py = piece
    sx, sy = slab_size
    for x in range(0, int(sx - px + 1)):
        for y in range(0, int(sy - py + 1)):
            overlap = False
            for (ox, oy, ow, oh) in placed:
                if not (x + px + MIN_GAP <= ox or x >= ox + ow + MIN_GAP or y + py + MIN_GAP <= oy or y >= oy + oh + MIN_GAP):
                    overlap = True
                    break
            if not overlap:
                return (x, y)
    return None

def pack_slabs_with_gap(pieces, slab_size):
    slabs = []
    for piece in pieces:
        w, h, rid, label = piece
        placed_successfully = False
        for slab in slabs:
            position = can_place_with_gap((w, h), slab, slab_size)
            if position:
                x, y = position
                slab.append((x, y, w, h, rid))
                placed_successfully = True
                break
        if not placed_successfully:
            # Try rotating the piece
            rotated = (h, w)
            for slab in slabs:
                position = can_place_with_gap(rotated, slab, slab_size)
                if position:
                    x, y = position
                    slab.append((x, y, rotated[0], rotated[1], rid))
                    placed_successfully = True
                    break
        if not placed_successfully:
            # New slab
            slabs.append([(0, 0, w, h, rid)])
    return slabs

    bins = pack_slabs_with_gap(pieces, (slab_length_in, slab_width_in))

        bins_dict = {}
    for slab_index, slab_parts in enumerate(bins):
        for part in slab_parts:
            x, y, w, h, rid = part
            if slab_index not in bins_dict:
                bins_dict[slab_index] = []
            bins_dict[slab_index].append((x, y, w, h, rid))
        
            bins = [bins_dict[k] for k in sorted(bins_dict.keys())]

    total_slab_area = len(bins) * slab_length_in * slab_width_in
    waste_area = total_slab_area - total_countertop_area

    st.success(f"You will need {len(bins)} slabs")
    st.info(f"Total countertop area: {total_countertop_area / 144:.2f} sq ft")
    st.info(f"Total slab area used: {total_slab_area / 144:.2f} sq ft")
    st.info(f"Waste area: {waste_area / 144:.2f} sq ft")

    pdf_bytes = io.BytesIO()
    with PdfPages(pdf_bytes) as pdf:
        for idx, slab_parts in enumerate(bins):
            fig, ax = plt.subplots(figsize=(36, 24))
            ax.set_xlim(0, slab_length_in)
            ax.set_ylim(0, slab_width_in)
            ax.set_aspect('equal')
            ax.set_title(f"Slab {idx + 1}")
            for x, y, w, h, rid in slab_parts:
                label = label_lookup.get(rid, "")
                rect = plt.Rectangle((x, y), w, h, facecolor='skyblue', edgecolor='blue')
                ax.add_patch(rect)
                ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=10)
            ax.invert_yaxis()
            pdf.savefig(fig)
            plt.close()

    st.download_button("📄 Download Slab Layout PDF", data=pdf_bytes.getvalue(), file_name="slab_layout_optimized.pdf", mime="application/pdf")
