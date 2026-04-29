import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

TOKEN = "3fd9730696d6408da6df2e9e342f8952"
SHOP_ID = "30224071"

def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        resp = requests.get(url, params=base_params, timeout=15)
        return resp.json() if resp.status_code == 200 else {"error": resp.status_code, "text": resp.text}
    except Exception as e:
        return {"error": "Connection", "text": str(e)}

# --- 2. TẢI DỮ LIỆU ---

# Bước A: Lấy toàn bộ đơn hàng (KHÔNG LỌC NGÀY để kiểm tra)
order_res = fetch_pancake_data("orders", {"limit": 50, "mode": "all"})
all_orders_raw = order_res.get("data", [])

# Bước B: Lấy danh sách phiếu nhập (Thử cả 2 đường dẫn)
purchase_res = fetch_pancake_data("purchase_orders", {"limit": 50})
if not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 50})
purchase_data = purchase_res.get("data", [])

# Bước C: Lấy tồn kho sản phẩm
inventory_res = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100})
inventory_data = inventory_res.get("data", [])

# --- 3. GIAO DIỆN ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Khu vực Debug (Chỉ hiện khi dữ liệu trống)
if not all_orders_raw and not purchase_data:
    with st.expander("🔍 Kiểm tra lỗi kỹ thuật (Debug)"):
        st.write("Phản hồi từ API Đơn hàng:", order_res)
        st.write("Phản hồi từ API Nhập hàng:", purchase_res)
        st.info("Nếu kết quả trên là {'data': []}, nghĩa là Key này không có quyền xem dữ liệu của shop.")

tab1, tab2, tab3, tab4 = st.tabs(["📑 Đơn hàng (Toàn bộ)", "📥 Nhập hàng", "📈 Tồn kho", "⚙️ Cài đặt"])

with tab1:
    if all_orders_raw:
        st.success(f"Đã tìm thấy {len(all_orders_raw)} đơn hàng!")
        st.dataframe(pd.DataFrame(all_orders_raw), use_container_width=True)
    else:
        st.warning("Danh sách đơn hàng trống. Hãy kiểm tra mục Debug bên trên.")

with tab2:
    if purchase_data:
        st.dataframe(pd.DataFrame(purchase_data), use_container_width=True)
    else:
        st.info("Không có dữ liệu phiếu nhập.")

with tab3:
    if inventory_data:
        st.dataframe(pd.DataFrame(inventory_data), use_container_width=True)
    else:
        st.info("Không có dữ liệu tồn kho.")
