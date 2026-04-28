import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake Full Data Extraction", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
    st.stop()

# --- THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_data():
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/orders"
    params = {"access_token": TOKEN, "limit": 100, "mode": "all"}
    try:
        resp = requests.get(url, params=params)
        return resp.json().get("data", []) if resp.status_code == 200 else []
    except: return []

data = fetch_data()

if data:
    # --- 1. XỬ LÝ THÔNG TIN CHUNG (ORDERS) ---
    all_orders = []
    # --- 2. XỬ LÝ CHI TIẾT SẢN PHẨM (ITEMS) ---
    all_items = []

    for order in data:
        # Nhóm 1 & 2 & 4: Thông tin chung, Tiền đơn hàng, Khách hàng, Nhân viên
        order_info = {
            "Mã đơn (ID)": order.get('id'),
            "Mã hiển thị": order.get('display_id'),
            "Mã tùy chỉnh": order.get('custom_id'),
            "Trạng thái": order.get('status'),
            "Ngày tạo": order.get('inserted_at'),
            "Tên khách": order.get('bill_full_name'),
            "SĐT khách": order.get('bill_phone_number'),
            "Nguồn": order.get('ads_source'),
            "Nhân viên tạo": order.get('creator', {}).get('name'),
            # --- CÁC TRƯỜNG LIÊN QUAN ĐẾN TIỀN (CHUNG) ---
            "Tổng tiền (total_price)": order.get('total_price'),
            "Tiền thu hộ (cod)": order.get('cod'),
            "Giảm giá (discount)": order.get('discount'),
            "Giảm giá tổng (total_discount)": order.get('total_discount'),
            "Phí ship (shipping_fee)": order.get('shipping_fee'),
            "Khách trả phí (customer_pay_fee)": order.get('customer_pay_fee'),
            "Tiền chuyển khoản (transfer_money)": order.get('transfer_money'),
            "Tiền mặt (cash)": order.get('cash')
        }
        all_orders.append(order_info)

        # Nhóm 3: Chi tiết từng sản phẩm
        items = order.get('items', [])
        if isinstance(items, list):
            for item in items:
                v_info = item.get('variation_info', {})
                all_items.append({
                    "Mã đơn": order.get('display_id'),
                    "Tên sản phẩm": v_info.get('name'),
                    "Chi tiết": v_info.get('detail'),
                    "Mã SKU": v_info.get('id'),
                    "Số lượng": item.get('quantity'),
                    # --- CÁC TRƯỜNG LIÊN QUAN ĐẾN GIÁ (ITEMS) ---
                    "Giá bán niêm yết (retail_price)": v_info.get('retail_price'),
                    "Giá nhập cuối (last_imported_price)": v_info.get('last_imported_price'),
                    "Giá bán sỉ (wholesale_price)": v_info.get('wholesale_price'),
                    "Vị trí kệ": item.get('variations_warehouses', [{}])[0].get('shelf_position'),
                    "Kho": order.get('warehouse_info', {}).get('name')
                })

    # Tạo DataFrame
    df_orders = pd.DataFrame(all_orders)
    df_items = pd.DataFrame(all_items)

    # --- HIỂN THỊ ---
    st.title("📊 Toàn bộ dữ liệu Pancake POS")

    # Tab để phân tách thông tin cho dễ nhìn
    tab1, tab2 = st.tabs(["📑 Thông tin Đơn hàng (Tiền & Chung)", "📦 Chi tiết Sản phẩm (Giá nhập/bán)"])

    with tab1:
        st.subheader("Toàn bộ các trường thông tin đơn hàng và tài chính")
        st.dataframe(df_orders, use_container_width=True)

    with tab2:
        st.subheader("Chi tiết từng sản phẩm, giá vốn và giá bán")
        st.dataframe(df_items, use_container_width=True)

else:
    st.info("Đang chờ dữ liệu từ Pancake...")
