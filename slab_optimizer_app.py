import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import tempfile
import os

# Default slab size in inches
DEFAULT_SLAB_WIDTH = 127
DEFAULT_SLAB_HEIGHT = 64

def load_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    expected_columns = {"Label", "Length (ft)", "Width (ft)", "Quantity"}
    if not expected_columns.issubset(df.columns):
        st.error("CSV must contain columns: Label, Length (ft), Width (ft), Quantity")
        return None
    return df

def generate_pieces(df):
    pieces = []
    label_map = {}
    for _, row in df.iterrows():
        label = row["Label"]
        length = float(row["Length (ft)"]) * 12
        width = float(row["Width (ft)"]) * 12
        qty = int(row["Quantity"])
        for _ in range(qty):
            pieces.append((length, width))
        label_map[(length, width)] = label
    return pieces, label_map

def can_place(piece, placed, slab_size, gap):
    pw, ph = map(int, piece)
    sw, sh = map(int, slab_size)
    for x in range(0, sw - pw + 1):
        for y in range(0, sh - ph + 1):
            overlap = False
            for (ox, oy, ow, oh) in placed:
                if not (x + pw + gap <= ox or x >= ox + ow + gap or y + ph + gap <= oy or y >= oy + oh + gap):
                    overlap = True
                    break
            if not overlap:
                return (x, y)
    return None

def pack_slabs(pieces, slab_size, gap):
    slabs = []
    for piece in pieces:
        placed = False
        for slab in slabs:
            pos = can_place(piece, slab, slab_size, gap)
            if pos:
                x, y = pos
                slab.append((x, y, piece[0], piece[1]))
                placed = True
                break
        if not placed:
            # Try rotated
            rotated = (piece[1], piece[0])
            for slab in slabs:
                pos = can_place(rotated, slab, slab_size, gap)
                if pos:
                    x, y = pos
                    slab.append((x, y, rotated[0], rotated[1]))
                    placed = True
                    break
        if not placed:
            slabs.append([(0, 0, piece[0], piece[1])])
    return slabs

def draw_slabs(slabs, slab_size, label_map):
    cols = 2
    rows = 3
    slabs_per_page = cols * rows
    pages = []

    for i in range(0, len(slabs), slabs_per_page):
        fig, axs = plt.subplots(rows, cols, figsize=(36, 24))
        axs = axs.flatten()
        for j, slab in enumerate(slabs[i:i+slabs_per_page]):
            ax = axs[j]
            ax.set_title(f"Slab {i + j + 1}", fontsize=18)
            ax.set_xlim(0, slab_size[0])
            ax.set_ylim(0, slab_size[1])
            ax.set_aspect('equal')
            for (x, y, w, h) in slab:
                label = label_map.get((w, h), label_map.get((h, w), '?'))
                rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor='skyblue')
                ax.add_patch(rect)
                ax.text(x + w / 2, y + h / 2, label, fontsize=12, ha='center', va='center')
            ax.invert_yaxis()
            ax.grid(True)
        for j in range(len(slabs[i:i+slabs_per_page]), len(axs)):
            axs[j].axis('off')
        plt.tight_layout()
        pages.append(fig)
    return pages

def save_pdf(pages):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with PdfPages(tmp_file.name) as pdf:
        for fig in pages:
            pdf.savefig(fig)
            plt.close(fig)
    return tmp_file.name

# Streamlit UI
st.title("Quartz Slab Layout Optimizer")

slab_width = st.number_input("Slab Width (in)", value=DEFAULT_SLAB_WIDTH)
slab_height = st.number_input("Slab Height (in)", value=DEFAULT_SLAB_HEIGHT)
gap = st.selectbox("Cutting Gap (in)", options=[0.5, 1.0], index=1)

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = load_csv(uploaded_file)
    if df is not None:
        st.dataframe(df)
        if st.button("Generate Layout"):
            pieces, label_map = generate_pieces(df)
            slabs = pack_slabs(pieces, (slab_width, slab_height), gap)
            st.success(f"Layout generated using {len(slabs)} slab(s)")
            pages = draw_slabs(slabs, (slab_width, slab_height), label_map)
            pdf_path = save_pdf(pages)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF Layout", f, file_name="slab_layout.pdf")
            os.remove(pdf_path)
else:
    st.info("Upload a CSV to begin. Must include: Label, Length (ft), Width (ft), Quantity")
