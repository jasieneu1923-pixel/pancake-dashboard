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
# Sử dụng API Key mới nhất bạn vừa cung cấp
TOKEN = "faea6078b156431fa19f7ac903dda137"
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
        return {"error": resp.status_code, "text": resp.text}
    except Exception as e:
        return {"error": "ConnectionError", "text": str(e)}

# --- 3. TẢI DỮ LIỆU ---

# A. Đơn hàng: Lấy từ ngày 24/04/2026
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

# B. Nhập hàng: Lấy toàn bộ lịch sử (Thử cả 2 endpoint dự phòng)
purchase_res = fetch_pancake_data("purchase_orders", {"limit": 100})
if not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 100})
purchase_data = purchase_res.get("data", [])

# C. Thống kê tồn kho: Lấy toàn bộ
stats_variant_raw = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100}).get("data", [])
stats_product_raw = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU CHI TIẾT ---

# --- BẢNG 1 & 2: ĐƠN HÀNG & SẢN PHẨM ---
all_orders, all_items = [], []
for order in all_orders_raw:
    custom_id = order.get('custom_id')
    all_orders.append({
        "Mã tùy chỉnh (Custom ID)": custom_id,
        "Tên Page": order.get('page', {}).get('name'),
        "Trạng thái (Số)": order.get('status'),
        "Ngày tạo": order.get('inserted_at'),
        "Tên khách": order.get('bill_full_name'),
        "SĐT khách": order.get('bill_phone_number'),
        "Tổng tiền": order.get('total_price'),
        "COD": order.get('cod'),
        "Nhân viên tạo": order.get('creator', {}).get('name')
    })
    for item in order.get('items', []):
        v_info = item.get('variation_info', {})
        all_items.append({
            "Mã đơn": custom_id,
            "Tên sản phẩm": v_info.get('name'),
            "Mã SKU": v_info.get('id'),
            "Số lượng": item.get('quantity'),
            "Giá niêm yết": v_info.get('retail_price'),
            "Giá nhập cuối": v_info.get('last_imported_price'),
            "Kho": order.get('warehouse_info', {}).get('name')
        })

# --- BẢNG 3: NHẬP HÀNG ---
list_purchase = []
status_map = {-1: "Mới", 0: "Đã xác nhận", 1: "Đã nhập hàng", 2: "Đã hủy"}
for p in purchase_data:
    p_status = status_map.get(p.get('status'), "N/A")
    for it in p.get('items', []):
        list_purchase.append({
            "Mã phiếu": p.get('display_id'),
            "Trạng thái": p_status,
            "Ngày nhập": p.get('time_import') or p.get('inserted_at'),
            "Nhà cung cấp": p.get('supplier', {}).get('name', 'N/A'),
            "Sản phẩm": it.get('product_name'),
            "SL Nhập": it.get('quantity'),
            "Giá nhập": it.get('imported_price'),
            "Còn nợ": p.get('total_remain_price'),
            "Người tạo": p.get('user', {}).get('name')
        })

# --- 5. HIỂN THỊ ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Kiểm tra dữ liệu
if not all_orders_raw and not purchase_data:
    st.warning("⚠️ Chú ý: Kết nối API thành công nhưng không tìm thấy dữ liệu. Hãy đảm bảo Key mới đã được chọn 'Tất cả các Page' khi tạo.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng (Từ 24/04)", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Thống kê Biến thể", "📈 Thống kê Sản phẩm"
])

with tab1:
    st.dataframe(pd.DataFrame(all_orders), use_container_width=True)
with tab2:
    st.dataframe(pd.DataFrame(all_items), use_container_width=True)
with tab3:
    st.dataframe(pd.DataFrame(list_purchase), use_container_width=True)
with tab4:
    st.dataframe(pd.DataFrame(stats_variant_raw), use_container_width=True)
with tab5:
    st.dataframe(pd.DataFrame(stats_product_raw), use_container_width=True)
