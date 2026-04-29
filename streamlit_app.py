import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
    st.stop()

# --- 2. THÔNG TIN API ---
TOKEN = "3fd9730696d6408da6df2e9e342f8952"
SHOP_ID = "30224071"

@st.cache_data(ttl=30) # Giảm thời gian cache để cập nhật dữ liệu nhanh hơn
def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        resp = requests.get(url, params=base_params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Lỗi {resp.status_code}", "detail": resp.text}
    except Exception as e:
        return {"error": "Lỗi kết nối", "detail": str(e)}

# --- 3. TẢI DỮ LIỆU (Cơ chế kiểm lỗi) ---

# A. Đơn hàng: Quét từ ngày 24/04/2026
# Thử định dạng thời gian đơn giản nhất (YYYY-MM-DD)
order_res = fetch_pancake_data("orders", {
    "limit": 50, 
    "mode": "all",
    "inserted_since": "2026-04-24 00:00:00" 
})
all_orders_raw = order_res.get("data", [])

# B. Nhập hàng: Thử cả 2 đường dẫn để tránh lỗi 404 (Lỗi bạn gặp trong Postman)
purchase_res = fetch_pancake_data("purchase_orders", {"limit": 100})
if "error" in purchase_res or not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 100})
purchase_data = purchase_res.get("data", [])

# C. Tồn kho
stats_v_raw = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100}).get("data", [])
stats_p_raw = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100}).get("data", [])

# --- 4. HIỂN THỊ VÀ KIỂM TRA ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Kiểm tra xem Key có hoạt động không
if "error" in order_res:
    st.error(f"❌ API Key không hợp lệ hoặc lỗi kết nối: {order_res.get('detail')}")
elif not all_orders_raw and not purchase_data:
    st.warning("⚠️ Kết nối thành công nhưng dữ liệu trả về Trống. Có thể do:")
    st.write("1. Không có đơn hàng/phiếu nhập nào từ ngày 24/04/2026.")
    st.write("2. API Key này chưa được tích quyền 'Xem đơn hàng' hoặc 'Kho'.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng (24/04)", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Tồn Biến thể", "📈 Tồn Sản phẩm"
])

with tab1:
    if all_orders_raw:
        st.dataframe(pd.DataFrame(all_orders_raw), use_container_width=True)
    else:
        st.info("Chưa có đơn hàng nào được tìm thấy từ ngày 24/04.")

with tab3:
    if purchase_data:
        st.dataframe(pd.DataFrame(purchase_data), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Nhập hàng (Lấy toàn bộ thời gian).")

with tab4:
    if stats_v_raw:
        st.dataframe(pd.DataFrame(stats_v_raw), use_container_width=True)

with tab5:
    if stats_p_raw:
        st.dataframe(pd.DataFrame(stats_p_raw), use_container_width=True)
