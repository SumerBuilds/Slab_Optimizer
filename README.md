# Quartz Slab Layout Optimizer

This is a Streamlit web app that helps you optimize quartz slab usage for countertop and surface cutting, minimizing waste and number of slabs needed.

## 🔧 Features

- Upload CSV with part dimensions and labels
- Supports slab sizing and blade cutting gap
- Automatically optimizes layout
- Generates downloadable PDF layout with labels
- Hosted on Streamlit Cloud (free)

---

## 📁 Sample CSV Format

The uploaded CSV should have the following columns:

```csv
Label,Length (ft),Width (ft),Quantity
island top,7,3.5,8
island side,3,3.5,16
kitchen 1,2.75,2,8
kitchen 2,5.5,2,8
bath 1,9.1,1.75,8
bath 2,2,1.75,8
```

---

## 🚀 Deploy Your Own

1. **Fork or clone this repository**
2. Make sure these files are in the root folder:
   - `app.py`
   - `requirements.txt`
   - (Optional) `sample_input.csv`
3. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
4. Click **“New app”**
5. Select this repo and set the file path to `app.py`
6. Click **“Deploy”**

---

## 🧪 Run Locally

Install dependencies and run the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📤 Output

The app generates a multi-page PDF showing each slab layout, labeled by part name and size.

---

## 🛠 Technologies

- Python
- Streamlit
- Matplotlib
- Pandas

---

## 📝 License

This tool is provided as-is for personal and professional use. No warranty provided.
