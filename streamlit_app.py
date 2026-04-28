import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH GIAO DIỆN & BẢO MẬT ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

st.sidebar.header("⚙️ QUẢN LÝ & BỘ LỌC")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để truy cập hệ thống.")
    st.stop()

# --- 2. THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, extra_params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    params = {"access_token": TOKEN}
    if extra_params: params.update(extra_params)
    try:
        resp = requests.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}
    except: return {}

# --- 3. TẢI DỮ LIỆU ---

# Tải Đơn hàng (Lấy 3 trang ~ 300 đơn gần nhất)
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    if batch.get("data"):
        all_orders_raw.extend(batch["data"])
    else: break

# Tải Nhập hàng (Purchase Orders)
purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 50}).get("data", [])

# Tải Tồn kho (Variations) - Theo cấu trúc JSON bạn gửi
inventory_raw = fetch_pancake_data("variations", {"limit": 100, "is_get_inventory": "true"}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# Bảng 1 & 2: Đơn hàng & Chi tiết sản phẩm trong đơn
df_orders = pd.DataFrame()
df_order_items = pd.DataFrame()

if all_orders_raw:
    orders_data, items_in_orders = [], []
    for order in all_orders_raw:
        custom_id = order.get('custom_id')
        # Xử lý bảng Đơn hàng & Tài chính
        orders_data.append({
            "Mã tùy chỉnh (Custom ID)": custom_id,
            "Tên Page": order.get('page', {}).get('name'),
            "Ngày tạo": order.get('inserted_at'),
            "Ngày cập nhật": order.get('updated_at'),
            "Tên khách": order.get('bill_full_name'),
            "SĐT khách": order.get('bill_phone_number'),
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
        # Xử lý bảng Chi tiết Sản phẩm & Mã định danh (Dùng Custom ID)
        for item in order.get('items', []):
            v_info = item.get('variation_info', {})
            items_in_orders.append({
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
    df_orders = pd.DataFrame(orders_data)
    df_order_items = pd.DataFrame(items_in_orders)

    # --- BỘ LỌC TẠI SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 TÌM KIẾM ĐƠN HÀNG")
    search_id = st.sidebar.text_input("Tìm theo Custom ID")
    search_phone = st.sidebar.text_input("Tìm theo SĐT khách")
    
    if search_id:
        df_orders = df_orders[df_orders['Mã tùy chỉnh (Custom ID)'].astype(str).str.contains(search_id, case=False, na=False)]
    if search_phone:
        df_orders = df_orders[df_orders['SĐT khách'].astype(str).str.contains(search_phone, na=False)]
    
    # Đồng bộ bảng sản phẩm theo bộ lọc
    df_order_items = df_order_items[df_order_items['Mã đơn (Custom ID)'].isin(df_orders['Mã tùy chỉnh (Custom ID)'])]

# Bảng 3: Nhập hàng (Purchase Orders)
df_purchase = pd.DataFrame([{
    "Mã phiếu nhập": p.get('display_id'),
    "Ngày tạo": p.get('inserted_at'),
    "Ngày nhập thực tế": p.get('received_at'),
    "Trạng thái": p.get('status_name'),
    "Nhà cung cấp": p.get('supplier', {}).get('name'),
    "Kho nhận": p.get('warehouse', {}).get('name'),
    "Tổng tiền hàng": p.get('total_price'),
    "Đã trả NCC": p.get('total_paid'),
    "Còn nợ": p.get('total_price', 0) - p.get('total_paid', 0),
    "Người tạo": p.get('creator', {}).get('name'),
    "Ghi chú": p.get('note')
} for p in purchase_raw])

# Bảng 4: Tồn kho chi tiết (Xử lý theo JSON thực tế bạn cung cấp)
inventory_processed = []
for v in inventory_raw:
    # Tách Màu và Size từ mảng fields
    fields = v.get('fields', [])
    attr_map = {f.get('name').lower(): f.get('value') for f in fields}
    
    # Lấy thông tin kho đầu tiên
    wh = v.get('variations_warehouses', [{}])[0]
    
    # Lấy giá sỉ từ price_table
    ptable = v.get('price_table', [])
    v_wholesale = next((p.get('price') for p in ptable if "sỉ" in p.get('name', '').lower()), 0)

    inventory_processed.append({
        "Mã SKU": v.get('display_id'),
        "Tên sản phẩm": v.get('product', {}).get('name'),
        "Màu": attr_map.get('màu', ''),
        "Size": attr_map.get('size', ''),
        "Tồn khả dụng": v.get('remain_quantity'),
        "Tồn thực tế kho": wh.get('actual_remain_quantity', 0),
        "Tổng tồn": wh.get('total_quantity', 0),
        "Hàng đang về": wh.get('pending_quantity', 0),
        "Giá nhập TB": v.get('average_imported_price'),
        "Giá nhập cuối": v.get('last_imported_price'),
        "Giá bán lẻ": v.get('retail_price'),
        "Giá bán sỉ": v_wholesale,
        "Barcode": v.get('barcode'),
        "Cập nhật cuối": v.get('updated_at')
    })
df_inventory = pd.DataFrame(inventory_processed)

# --- 5. HIỂN THỊ ---
st.title("🚀 Hệ thống Quản trị Tổng thể Pancake POS")

tab1, tab2, tab3, tab4 = st.tabs([
    "📑 Đơn hàng & Tài chính", 
    "📦 Chi tiết Sản phẩm Đơn", 
    "📥 Lịch sử Nhập hàng", 
    "🏠 Tồn kho chi tiết"
])

with tab1:
    st.subheader("Bảng tổng hợp Đơn hàng và Tài chính chi tiết")
    st.dataframe(df_orders, use_container_width=True)

with tab2:
    st.subheader("Bảng kê Sản phẩm theo mã định danh (Custom ID)")
    st.dataframe(df_order_items, use_container_width=True)

with tab3:
    st.subheader("Lịch sử các Phiếu nhập kho")
    st.dataframe(df_purchase, use_container_width=True)

with tab4:
    st.subheader("Dữ liệu Tồn kho chi tiết từng SKU")
    st.dataframe(df_inventory, use_container_width=True)

if not all_orders_raw and not inventory_raw:
    st.info("Đang tải dữ liệu từ API...")
