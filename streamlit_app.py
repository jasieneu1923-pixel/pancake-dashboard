import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full Data", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ CẤU HÌNH")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu để xem dữ liệu.")
    st.stop()

# --- THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, extra_params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    params = {"access_token": TOKEN}
    if extra_params: params.update(extra_params)
    try:
        resp = requests.get(url, params=params)
        return resp.json().get("data", []) if resp.status_code == 200 else []
    except: return []

# --- 1. LẤY DỮ LIỆU NHẬP HÀNG (PURCHASE ORDERS) ---
# API: /shops/:shop_id/purchase_orders
purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 100})

# --- 2. LẤY DỮ LIỆU TỒN KHO CHI TIẾT (VARIATIONS) ---
# API: /shops/:shop_id/variations
inventory_raw = fetch_pancake_data("variations", {"limit": 100, "is_get_inventory": "true"})

# --- XỬ LÝ BẢNG NHẬP HÀNG ---
purchase_list = []
for p in purchase_raw:
    purchase_list.append({
        "ID Phiếu": p.get('id'),
        "Mã hiển thị": p.get('display_id'),
        "Ngày tạo": p.get('inserted_at'),
        "Ngày nhập": p.get('received_at'),
        "Trạng thái": p.get('status_name'),
        "Nhà cung cấp": p.get('supplier', {}).get('name'),
        "SĐT NCC": p.get('supplier', {}).get('phone_number'),
        "Kho nhận": p.get('warehouse', {}).get('name'),
        "Tổng số lượng": p.get('total_quantity'),
        "Tổng tiền hàng": p.get('total_price'),
        "Đã trả": p.get('total_paid'),
        "Còn nợ": p.get('total_price', 0) - p.get('total_paid', 0),
        "Chiết khấu phiếu": p.get('discount_value'),
        "Phí nhập hàng": p.get('shipping_fee'),
        "Người tạo": p.get('creator', {}).get('name'),
        "Ghi chú": p.get('note')
    })

# --- XỬ LÝ BẢNG TỒN KHO CHI TIẾT ---
inventory_list = []
for v in inventory_raw:
    # Lấy thông tin tồn kho theo từng kho nếu có
    inv = v.get('inventory', {})
    inventory_list.append({
        "Mã SKU": v.get('id'),
        "Tên sản phẩm": v.get('name'),
        "Chi tiết phân loại": v.get('detail'),
        "Mã SP gốc (Product ID)": v.get('product_id'),
        "Barcode": v.get('barcode'),
        # Các trường tồn kho chi tiết
        "Tồn thực tế (Quantity)": inv.get('quantity', 0),
        "Sẵn sàng bán (Available)": inv.get('available_quantity', 0),
        "Hàng đang về (Incoming)": inv.get('incoming_quantity', 0),
        "Đang chuyển kho": inv.get('shipping_quantity', 0),
        "Khách đang giữ (Holding)": inv.get('holding_quantity', 0),
        "Đã hỏng/mất": inv.get('damaged_quantity', 0),
        # Thông tin giá
        "Giá nhập gần nhất": v.get('last_imported_price'),
        "Giá bán lẻ": v_info.get('retail_price') if 'v_info' in locals() else v.get('retail_price'),
        "Giá bán sỉ": v.get('wholesale_price'),
        "Khối lượng (gram)": v.get('weight'),
        "Vị trí kệ": v.get('warehouse_info', {}).get('shelf_position')
    })

df_purchase = pd.DataFrame(purchase_list)
df_inventory = pd.DataFrame(inventory_list)

# --- HIỂN THỊ ---
st.title("📑 Quản lý Nhập hàng & Tồn kho chi tiết")

tab1, tab2 = st.tabs(["📥 Lịch sử Nhập hàng", "🏠 Tồn kho chi tiết"])

with tab1:
    st.subheader("Danh sách Phiếu nhập kho")
    if not df_purchase.empty:
        st.dataframe(df_purchase, use_container_width=True)
        # Thêm nút tải Excel nếu cần
    else:
        st.info("Chưa có dữ liệu phiếu nhập.")

with tab2:
    st.subheader("Dữ liệu tồn kho chi tiết từng SKU")
    if not df_inventory.empty:
        # Highlight nếu tồn kho thấp (ví dụ < 5)
        st.dataframe(df_inventory, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu tồn kho.")
