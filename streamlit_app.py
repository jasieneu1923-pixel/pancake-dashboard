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
# Sử dụng API Key từ hình image_325fdb.png
TOKEN = "2b10f2b9145f4b779e30bd635084f5be" 
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        resp = requests.get(url, params=base_params)
        # Trả về dữ liệu nếu thành công, nếu lỗi 404 hoặc khác thì trả về dict trống
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

# --- 3. TẢI DỮ LIỆU ---

# A. Đơn hàng (Lấy 2 trang gần nhất để đảm bảo có dữ liệu)
all_orders_raw = []
for p in range(1, 3):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    data = batch.get("data", [])
    if not data: break
    all_orders_raw.extend(data)

# B. Nhập hàng (Sửa lỗi 404 bằng cách thử cả 2 đường dẫn)
purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 50})
if not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("purchase_orders", {"limit": 50})
purchase_data = purchase_res.get("data", [])

# C. Thống kê tồn kho
stats_variant_raw = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100}).get("data", [])
stats_product_raw = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# Xử lý Đơn hàng & Sản phẩm chi tiết
all_orders, all_items = [], []
for order in all_orders_raw:
    custom_id = order.get('custom_id')
    all_orders.append({
        "Mã tùy chỉnh": custom_id,
        "Trạng thái": order.get('status'),
        "Ngày tạo": order.get('inserted_at'),
        "Tên khách": order.get('bill_full_name'),
        "SĐT": order.get('bill_phone_number'),
        "Tổng tiền": order.get('total_price'),
        "COD": order.get('cod'),
        "Nhân viên": order.get('creator', {}).get('name')
    })
    for item in order.get('items', []):
        v_info = item.get('variation_info', {})
        all_items.append({
            "Mã đơn": custom_id,
            "Tên sản phẩm": v_info.get('name'),
            "Màu/Size": v_info.get('detail'),
            "Số lượng": item.get('quantity'),
            "Giá bán": v_info.get('retail_price'),
            "Giá nhập cuối": v_info.get('last_imported_price')
        })

# Xử lý phiếu Nhập hàng (Bảng 3)
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
            "Tổng giá trị phiếu": p.get('total_price'),
            "Còn nợ NCC": p.get('total_remain_price')
        })

# Xử lý Thống kê Tồn kho (Bảng 4 & 5)
list_stats_v = [{"Tên": s.get('variation', {}).get('name'), "Tồn cuối": s.get('end_inventory'), "Giá trị tồn": s.get('end_inventory_value')} for s in stats_variant_raw]
list_stats_p = [{"Tên SP": s.get('product', {}).get('name'), "Tổng nhập": s.get('total_import'), "Tổng xuất": s.get('total_export'), "Tồn hiện tại": s.get('end_inventory')} for s in stats_product_raw]

# --- 5. HIỂN THỊ GIAO DIỆN ---
st.title("📊 Hệ thống Quản trị Pancake POS")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Tồn Biến thể", "📈 Tồn Sản phẩm"
])

with tab1:
    st.dataframe(pd.DataFrame(all_orders), use_container_width=True)

with tab2:
    st.dataframe(pd.DataFrame(all_items), use_container_width=True)

with tab3:
    if list_purchase:
        st.dataframe(pd.DataFrame(list_purchase), use_container_width=True)
    else:
        st.info("Không lấy được dữ liệu Nhập hàng. Hãy đảm bảo bạn đã tạo phiếu nhập trên Pancake POS.")

with tab4:
    st.dataframe(pd.DataFrame(list_stats_v), use_container_width=True)

with tab5:
    st.dataframe(pd.DataFrame(list_stats_p), use_container_width=True)
