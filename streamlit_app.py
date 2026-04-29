import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Token mới bạn vừa cung cấp
TOKEN = "3fd9730696d6408da6df2e9e342f8952"
SHOP_ID = "30224071"

@st.cache_data(ttl=30)
def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        # Tăng timeout lên 15s để tránh lỗi mạng
        resp = requests.get(url, params=base_params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.status_code, "text": resp.text}
    except Exception as e:
        return {"error": "ConnectionError", "text": str(e)}

# --- 2. TẢI DỮ LIỆU ---

# A. Đơn hàng: Quét từ ngày 24/04/2026 (Dùng định dạng YYYY-MM-DD)
order_res = fetch_pancake_data("orders", {
    "limit": 50, 
    "mode": "all",
    "inserted_since": "2026-04-24 00:00:00"
})
all_orders_raw = order_res.get("data", [])

# B. Nhập hàng: Tự động sửa lỗi 404 bằng cách thử cả 2 endpoint phổ biến
purchase_res = fetch_pancake_data("purchase_orders", {"limit": 100})
if "error" in purchase_res or not purchase_res.get("data"):
    # Endpoint dự phòng nếu cái đầu bị 404 như trong Postman của bạn
    purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 100})
purchase_data = purchase_res.get("data", [])

# C. Tồn kho: Lấy toàn bộ thống kê
stats_v_res = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100})
stats_p_res = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100})
stats_v_raw = stats_v_res.get("data", [])
stats_p_raw = stats_p_res.get("data", [])

# --- 3. HIỂN THỊ ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Kiểm tra trạng thái Key
if "error" in order_res and order_res["error"] == 401:
    st.error("❌ API Key không hợp lệ hoặc đã hết hạn.")
elif not all_orders_raw and not purchase_data and not stats_p_raw:
    st.warning("⚠️ Kết nối OK nhưng không có dữ liệu trả về. Hãy kiểm tra Shop ID hoặc quyền hạn của Key.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng (24/04)", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Tồn Biến thể", "📈 Tồn Sản phẩm"
])

with tab1:
    if all_orders_raw:
        st.dataframe(pd.DataFrame(all_orders_raw), use_container_width=True)
    else:
        st.info("Không tìm thấy đơn hàng nào từ ngày 24/04/2026.")

with tab3:
    if purchase_data:
        st.dataframe(pd.DataFrame(purchase_data), use_container_width=True)
    else:
        st.info("Dữ liệu Nhập hàng trống (Đã thử nghiệm các đường dẫn dự phòng).")

with tab5:
    if stats_p_raw:
        st.dataframe(pd.DataFrame(stats_p_raw), use_container_width=True)
    else:
        st.info("Dữ liệu Tồn sản phẩm trống.")
