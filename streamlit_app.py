import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full Data System", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
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

# --- 3. TẢI DỮ LIỆU ĐA NGUỒN ---

# A. Lấy dữ liệu Đơn hàng (Vòng lặp lấy nhiều trang)
all_orders_raw = []
pages_to_fetch = 5 # Bạn có thể chỉnh lên 10 để lấy 1000 đơn
for p in range(1, pages_to_fetch + 1):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    page_data = batch.get("data", [])
    if not page_data: break
    all_orders_raw.extend(page_data)

# B. Lấy dữ liệu Sản phẩm & Tồn kho (Product List / Variations)
product_resp = fetch_pancake_data("variations", {"limit": 100, "is_get_inventory": "true"})
product_raw = product_resp.get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# --- BẢNG 1 & 2: GIỮ NGUYÊN TỪ CODE CŨ ---
list_orders = []
list_item_orders = []

for order in all_orders_raw:
    custom_id = order.get('custom_id')
    # Thông tin tài chính
    list_orders.append({
        "Mã tùy chỉnh (Custom ID)": custom_id,
        "Tên Page": order.get('page', {}).get('name'),
        "Page ID": order.get('page_id'),
        "Trạng thái (Số)": order.get('status'),
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
    # Chi tiết sản phẩm trong đơn
    items = order.get('items', [])
    if isinstance(items, list):
        for item in items:
            v_info = item.get('variation_info', {})
            list_item_orders.append({
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

# --- BẢNG 3 & 4: SẢN PHẨM & TỒN KHO (THEO JSON MỚI) ---
list_products = []
list_inventory_detail = []

for v in product_raw:
    # Xử lý Màu/Size từ fields
    fields = v.get('fields') or []
    attr_map = {str(f.get('name', '')).lower(): f.get('value') for f in fields if isinstance(f, dict)}
    
    # Xử lý Giá sỉ từ price_table
    ptable = v.get('price_table') or []
    v_wholesale = 0
    if isinstance(ptable, list):
        v_wholesale = next((p.get('price') for p in ptable if isinstance(p, dict) and "sỉ" in str(p.get('name', '')).lower()), 0)

    # Bảng 3: Thông tin sản phẩm (Biến thể)
    list_products.append({
        "Mã SKU": v.get('display_id'),
        "Tên sản phẩm": v.get('product', {}).get('name') if v.get('product') else "N/A",
        "Màu": attr_map.get('màu', ''),
        "Size": attr_map.get('size', ''),
        "Giá bán lẻ": v.get('retail_price', 0),
        "Giá bán sỉ": v_wholesale,
        "Giá tại quầy": v.get('price_at_counter'),
        "Giá nhập TB": v.get('average_imported_price'),
        "Giá nhập cuối": v.get('last_imported_price'),
        "Barcode": v.get('barcode'),
        "Bán âm": "Cho phép" if v.get('is_sell_negative_variation') else "Không",
        "Ngày tạo SP": v.get('inserted_at')
    })

    # Bảng 4: Tồn kho thực tế từng chi nhánh
    warehouses = v.get('variations_warehouses') or []
    for wh in warehouses:
        list_inventory_detail.append({
            "Mã SKU": v.get('display_id'),
            "Warehouse ID": wh.get('warehouse_id'),
            "Tồn thực tế": wh.get('actual_remain_quantity'),
            "Tồn khả dụng": wh.get('remain_quantity'),
            "Hàng đang về": wh.get('pending_quantity'),
            "Tổng tồn": wh.get('total_quantity'),
            "Tốc độ bán TB": wh.get('selling_avg')
        })

# Chuyển đổi thành DataFrame
df_orders = pd.DataFrame(list_orders)
df_items = pd.DataFrame(list_item_orders)
df_products = pd.DataFrame(list_products)
df_inventory = pd.DataFrame(list_inventory_detail)

# --- 5. HIỂN THỊ ---
st.title("📊 Hệ thống Quản trị & Trích xuất Dữ liệu Pancake POS")
st.info(f"Dữ liệu hiện tại: {len(df_orders)} Đơn hàng | {len(df_products)} Sản phẩm biến thể.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📑 Đơn hàng & Tài chính", 
    "📦 Sản phẩm trong đơn", 
    "💎 Danh mục Sản phẩm (SKU)",
    "🏠 Tồn kho chi tiết"
])

with tab1:
    st.subheader("Bảng tổng hợp Đơn hàng & Tài chính")
    st.dataframe(df_orders, use_container_width=True)

with tab2:
    st.subheader("Bảng kê chi tiết sản phẩm theo mã đơn")
    st.dataframe(df_items, use_container_width=True)

with tab3:
    st.subheader("Danh mục Sản phẩm, Thuộc tính & Giá")
    st.dataframe(df_products, use_container_width=True)

with tab4:
    st.subheader("Phân bổ tồn kho thực tế theo kho/chi nhánh")
    st.dataframe(df_inventory, use_container_width=True)
