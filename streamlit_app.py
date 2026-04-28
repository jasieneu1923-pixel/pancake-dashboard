import streamlit as st
import requests
import pandas as pd

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Sidebar bảo mật & Bộ lọc
st.sidebar.header("⚙️ QUẢN LÝ & BỘ LỌC")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu để sử dụng hệ thống.")
    st.stop()

# --- THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

# --- HÀM GỌI API ---
@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, extra_params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    params = {"access_token": TOKEN}
    if extra_params: params.update(extra_params)
    try:
        resp = requests.get(url, params=params)
        return resp.json().get("data", []) if resp.status_code == 200 else []
    except: return []

# 1. Tải Đơn hàng (Vòng lặp lấy 5 trang ~ 500 đơn)
all_orders_raw = []
for p in range(1, 6):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    if not batch: break
    all_orders_raw.extend(batch)

# 2. Tải Nhập hàng (Purchase Orders)
purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 100})

# 3. Tải Tồn kho (Variations)
inventory_raw = fetch_pancake_data("variations", {"limit": 100, "is_get_inventory": "true"})

# --- XỬ LÝ DỮ LIỆU ---

# Bảng 1 & 2: Đơn hàng và Chi tiết sản phẩm đơn
if all_orders_raw:
    all_orders_list, all_order_items = [], []
    for order in all_orders_raw:
        custom_id = order.get('custom_id')
        # Bảng Đơn hàng
        all_orders_list.append({
            "Mã tùy chỉnh (Custom ID)": custom_id,
            "Tên Page": order.get('page', {}).get('name'),
            "Page ID": order.get('page_id'),
            "Trạng thái (Số)": order.get('status'),
            "Ngày tạo": order.get('inserted_at'),
            "Ngày cập nhật": order.get('updated_at'),
            "Tên khách": order.get('bill_full_name', ''),
            "SĐT khách": order.get('bill_phone_number', ''),
            "Nhân viên tạo": order.get('creator', {}).get('name'),
            "Nhân viên cập nhật cuối": order.get('updator', {}).get('name'),
            "Tổng tiền (Total Price)": order.get('total_price'),
            "Tiền thu hộ (COD)": order.get('cod'),
            "Giảm giá đơn (Discount)": order.get('discount'),
            "Tổng giảm giá (Total Discount)": order.get('total_discount'),
            "Phí ship báo khách (Shipping Fee)": order.get('shipping_fee'),
            "Khách trả phí (Customer Pay Fee)": order.get('customer_pay_fee'),
            "Tiền chuyển khoản": order.get('transfer_money'),
            "Tiền mặt": order.get('cash'),
            "Nguồn Ads": order.get('ads_source')
        })
        # Bảng Chi tiết sản phẩm trong đơn
        for item in order.get('items', []):
            v_info = item.get('variation_info', {})
            all_order_items.append({
                "Mã đơn (Custom ID)": custom_id,
                "Tên sản phẩm": v_info.get('name'),
                "Chi tiết": v_info.get('detail'),
                "Mã SKU (Var ID)": v_info.get('id'),
                "Mã SP Gốc (Prod ID)": v_info.get('product_id'),
                "Số lượng": item.get('quantity'),
                "Giá bán niêm yết": v_info.get('retail_price'),
                "Giá nhập cuối": v_info.get('last_imported_price'),
                "Tên Kho": order.get('warehouse_info', {}).get('name')
            })
    df_orders = pd.DataFrame(all_orders_list)
    df_order_items = pd.DataFrame(all_order_items)

    # --- BỘ LỌC TẠI SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 TÌM KIẾM ĐƠN HÀNG")
    search_id = st.sidebar.text_input("Tìm Custom ID")
    search_phone = st.sidebar.text_input("Tìm Số điện thoại")
    
    if search_id:
        df_orders = df_orders[df_orders['Mã tùy chỉnh (Custom ID)'].astype(str).str.contains(search_id, case=False, na=False)]
    if search_phone:
        df_orders = df_orders[df_orders['SĐT khách'].astype(str).str.contains(search_phone, na=False)]
    
    # Đồng bộ bảng chi tiết sản phẩm theo bộ lọc
    df_order_items = df_order_items[df_order_items['Mã đơn (Custom ID)'].isin(df_orders['Mã tùy chỉnh (Custom ID)'])]

# Bảng 3: Nhập hàng (Purchase Orders) - Full trường
df_purchase = pd.DataFrame([{
    "Mã phiếu nhập": p.get('display_id'),
    "Ngày tạo": p.get('inserted_at'),
    "Ngày nhập thực tế": p.get('received_at'),
    "Trạng thái": p.get('status_name'),
    "Nhà cung cấp": p.get('supplier', {}).get('name'),
    "Kho nhận": p.get('warehouse', {}).get('name'),
    "Tổng số lượng": p.get('total_quantity'),
    "Tổng tiền hàng": p.get('total_price'),
    "Đã trả NCC": p.get('total_paid'),
    "Chiết khấu phiếu": p.get('discount_value'),
    "Phí vận chuyển nhập": p.get('shipping_fee'),
    "Người tạo": p.get('creator', {}).get('name'),
    "Ghi chú": p.get('note')
} for p in purchase_raw])

# Bảng 4: Tồn kho chi tiết (Inventory) - Full trường
df_inventory = pd.DataFrame([{
    "Mã SKU": v.get('id'),
    "Tên sản phẩm": v.get('name'),
    "Phân loại": v.get('detail'),
    "Barcode": v.get('barcode'),
    "Tồn thực tế": v.get('inventory', {}).get('quantity', 0),
    "Sẵn sàng bán": v.get('inventory', {}).get('available_quantity', 0),
    "Hàng đang về": v.get('inventory', {}).get('incoming_quantity', 0),
    "Đang chuyển": v.get('inventory', {}).get('shipping_quantity', 0),
    "Khách giữ": v.get('inventory', {}).get('holding_quantity', 0),
    "Giá nhập gần nhất": v.get('last_imported_price'),
    "Giá bán lẻ": v.get('retail_price'),
    "Vị trí kệ": v.get('warehouse_info', {}).get('shelf_position')
} for v in inventory_raw])

# --- HIỂN THỊ TẤT CẢ CÁC BẢNG ---
st.title("📊 Hệ thống Quản trị Tổng thể Pancake POS")

tab1, tab2, tab3, tab4 = st.tabs([
    "📑 Đơn hàng & Tài chính", 
    "📦 Chi tiết Sản phẩm Đơn", 
    "📥 Lịch sử Nhập hàng", 
    "🏠 Tồn kho chi tiết"
])

with tab1:
    st.subheader("Bảng tổng hợp Đơn hàng")
    st.dataframe(df_orders, use_container_width=True)

with tab2:
    st.subheader("Bảng kê Sản phẩm theo đơn")
    st.dataframe(df_order_items, use_container_width=True)

with tab3:
    st.subheader("Danh sách Phiếu nhập kho (Purchase Orders)")
    st.dataframe(df_purchase, use_container_width=True)

with tab4:
    st.subheader("Bảng theo dõi Tồn kho khả dụng chi tiết")
    st.dataframe(df_inventory, use_container_width=True)
