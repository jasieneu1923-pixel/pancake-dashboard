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
    all_orders = []
    all_items = []

    for order in data:
        # 1. THÔNG TIN CHUNG & TÀI CHÍNH (Đã thêm Tên trạng thái & Ngày cập nhật)
        order_info = {
            "Mã hiển thị": order.get('display_id'),
            "Tên Page": order.get('page', {}).get('name'),
            "Page ID": order.get('page_id'),
            "Trạng thái (Số)": order.get('status'),
            "Tên trạng thái": order.get('status_name'), # Trường status_name từ JSON
            "Ngày tạo": order.get('inserted_at'),
            "Ngày cập nhật": order.get('updated_at'), # Trường updated_at từ JSON
            "Tên khách": order.get('bill_full_name'),
            "SĐT khách": order.get('bill_phone_number'),
            "Nguồn Ads": order.get('ads_source'),
            "Nhân viên tạo": order.get('creator', {}).get('name'),
            "Tổng tiền": order.get('total_price'),
            "Tiền thu hộ (COD)": order.get('cod'),
            "Giảm giá tổng": order.get('total_discount'),
            "Phí ship": order.get('shipping_fee'),
        }
        all_orders.append(order_info)

        # 2. CHI TIẾT SẢN PHẨM
        items = order.get('items', [])
        if isinstance(items, list):
            for item in items:
                v_info = item.get('variation_info', {})
                all_items.append({
                    "Mã đơn (Display)": order.get('display_id'),
                    "Tên sản phẩm": v_info.get('name'),
                    "Chi tiết": v_info.get('detail'),
                    "Mã SKU (Var ID)": v_info.get('id'),
                    "Mã SP Gốc (Prod ID)": v_info.get('product_id'),
                    "Số lượng": item.get('quantity'),
                    "Giá bán niêm yết": v_info.get('retail_price'),
                    "Giá nhập cuối": v_info.get('last_imported_price'),
                    "Tên Kho": order.get('warehouse_info', {}).get('name')
                })

    df_orders = pd.DataFrame(all_orders)
    df_items = pd.DataFrame(all_items)

    # --- HIỂN THỊ ---
    st.title("📊 Hệ thống Trích xuất Dữ liệu Pancake POS")
    tab1, tab2 = st.tabs(["📑 Đơn hàng & Tài chính", "📦 Chi tiết Sản phẩm & Mã định danh"])

    with tab1:
        st.subheader("Bảng tổng hợp Đơn hàng & Trạng thái mới nhất")
        st.dataframe(df_orders, use_container_width=True)

    with tab2:
        st.subheader("Bảng chi tiết Sản phẩm (SKU & Giá)")
        st.dataframe(df_items, use_container_width=True)

else:
    st.info("Đang chờ dữ liệu từ Pancake...")
