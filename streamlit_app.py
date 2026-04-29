import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
    st.stop()

# --- 2. THÔNG TIN API ---
# API Key mới bạn vừa cung cấp
TOKEN = "3fd9730696d6408da6df2e9e342f8952"
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        resp = requests.get(url, params=base_params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return {"error_code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"error_code": "Connection", "message": str(e)}

# --- 3. TẢI DỮ LIỆU ---

# A. Đơn hàng (Từ 24/04/2026)
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {
        "limit": 100, 
        "mode": "all", 
        "page": p,
        "inserted_since": "2026-04-24 00:00:00"
    })
    data = batch.get("data", [])
    if not data: break
    all_orders_raw.extend(data)

# B. Nhập hàng (Toàn bộ - Tự động sửa lỗi 404)
purchase_res = fetch_pancake_data("purchase_orders", {"limit": 100})
if not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 100})
purchase_data = purchase_res.get("data", [])

# C. Thống kê tồn kho (Toàn bộ)
stats_v_raw = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100}).get("data", [])
stats_p_raw = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100}).get("data", [])

# --- 4. XỬ LÝ VÀ HIỂN THỊ ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Kiểm tra nhanh kết nối
if not all_orders_raw and not purchase_data:
    st.error("⚠️ Không lấy được dữ liệu. Hãy kiểm tra xem API Key mới đã được tích quyền 'Đơn hàng' và 'Kho' chưa.")
    with st.expander("Chi tiết phản hồi từ POS"):
        st.write("Dữ liệu đơn hàng:", all_orders_raw)
        st.write("Dữ liệu nhập hàng:", purchase_data)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng (24/04)", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Tồn Biến thể", "📈 Tồn Sản phẩm"
])

with tab1:
    if all_orders_raw:
        df_o = pd.DataFrame([{
            "Mã tùy chỉnh": o.get('custom_id'),
            "Tên Page": o.get('page', {}).get('name'),
            "Trạng thái": o.get('status'),
            "Ngày tạo": o.get('inserted_at'),
            "Khách hàng": o.get('bill_full_name'),
            "SĐT": o.get('bill_phone_number'),
            "Tổng tiền": o.get('total_price'),
            "Nhân viên": o.get('creator', {}).get('name')
        } for o in all_orders_raw])
        st.dataframe(df_o, use_container_width=True)
    else: st.info("Trống: Không có đơn hàng từ 24/04.")

with tab3:
    if purchase_data:
        # Hiển thị toàn bộ cột nhập hàng
        list_p = []
        for p in purchase_data:
            for it in p.get('items', []):
                list_p.append({
                    "Mã phiếu": p.get('display_id'),
                    "Trạng thái": p.get('status'),
                    "Ngày nhập": p.get('time_import') or p.get('inserted_at'),
                    "Nhà cung cấp": p.get('supplier', {}).get('name'),
                    "Sản phẩm": it.get('product_name'),
                    "Số lượng": it.get('quantity'),
                    "Giá nhập": it.get('imported_price'),
                    "Còn nợ": p.get('total_remain_price')
                })
        st.dataframe(pd.DataFrame(list_p), use_container_width=True)
    else: st.info("Trống: Không có dữ liệu nhập hàng.")

with tab4:
    if stats_v_raw: st.dataframe(pd.DataFrame(stats_v_raw), use_container_width=True)

with tab5:
    if stats_p_raw: st.dataframe(pd.DataFrame(stats_p_raw), use_container_width=True)
