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
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    if batch.get("data"):
        all_orders_raw.extend(batch["data"])
    else: break

purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 50}).get("data", [])
inventory_raw = fetch_pancake_data("variations", {"limit": 100, "is_get_inventory": "true"}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# Bảng Đơn hàng & Sản phẩm
df_orders = pd.DataFrame()
df_order_items = pd.DataFrame()

if all_orders_raw:
    orders_data, items_in_orders = [], []
    for order in all_orders_raw:
        custom_id = order.get('custom_id')
        orders_data.append({
            "Mã tùy chỉnh (Custom ID)": custom_id,
            "Tên Page": order.get('page', {}).get('name'),
            "Ngày tạo": order.get('inserted_at'),
            "Tên khách": order.get('bill_full_name'),
            "SĐT khách": order.get('bill_phone_number'),
            "Tổng tiền (Total Price)": order.get('total_price'),
            "Tiền thu hộ (COD)": order.get('cod'),
            "Giảm giá đơn (Discount)": order.get('discount'),
            "Phí ship báo khách": order.get('shipping_fee'),
            "Tiền chuyển khoản": order.get('transfer_money'),
            "Tiền mặt": order.get('cash'),
            "Nhân viên tạo": order.get('creator', {}).get('name')
        })
        for item in order.get('items', []):
            v_info = item.get('variation_info', {})
            items_in_orders.append({
                "Mã đơn (Custom ID)": custom_id,
                "Tên sản phẩm": v_info.get('name'),
                "Chi tiết": v_info.get('detail'),
                "Mã SKU": v_info.get('id'),
                "Số lượng": item.get('quantity'),
                "Giá bán niêm yết": v_info.get('retail_price'),
                "Giá nhập cuối": v_info.get('last_imported_price')
            })
    df_orders = pd.DataFrame(orders_data)
    df_order_items = pd.DataFrame(items_in_orders)

# Bảng Nhập hàng
df_purchase = pd.DataFrame([{
    "Mã phiếu nhập": p.get('display_id'),
    "Nhà cung cấp": p.get('supplier', {}).get('name'),
    "Trạng thái": p.get('status_name'),
    "Tổng tiền": p.get('total_price'),
    "Đã trả NCC": p.get('total_paid'),
    "Ngày tạo": p.get('inserted_at')
} for p in purchase_raw])

# Bảng Tồn kho (ĐÃ SỬA LỖI INDEXERROR)
inventory_processed = []
for v in inventory_raw:
    fields = v.get('fields', [])
    attr_map = {f.get('name').lower(): f.get('value') for f in fields}
    
    # KIỂM TRA AN TOÀN TRƯỚC KHI TRUY CẬP [0]
    warehouses = v.get('variations_warehouses', [])
    wh = warehouses[0] if isinstance(warehouses, list) and len(warehouses) > 0 else {}
    
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
        "Giá nhập cuối": v.get('last_imported_price'),
        "Giá bán lẻ": v.get('retail_price'),
        "Giá bán sỉ": v_wholesale,
        "Barcode": v.get('barcode')
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

with tab1: st.dataframe(df_orders, use_container_width=True)
with tab2: st.dataframe(df_order_items, use_container_width=True)
with tab3: st.dataframe(df_purchase, use_container_width=True)
with tab4: st.dataframe(df_inventory, use_container_width=True)
