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
def fetch_all_data(pages_to_fetch=5): # Bạn có thể tăng số page muốn lấy ở đây
    all_data = []
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/orders"
    
    for page in range(1, pages_to_fetch + 1):
        params = {
            "access_token": TOKEN, 
            "limit": 100, 
            "mode": "all",
            "page": page
        }
        try:
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                page_data = resp.json().get("data", [])
                if not page_data: # Nếu trang đó không có dữ liệu thì dừng lại
                    break
                all_data.extend(page_data)
            else:
                break
        except:
            break
    return all_data

# Tăng số lượng trang muốn lấy tại đây (ví dụ: lấy 10 trang tương ứng ~1000 đơn)
data = fetch_all_data(pages_to_fetch=10) 

if data:
    all_orders = []
    all_items = []

    for order in data:
        custom_id = order.get('custom_id')

        # 1. THÔNG TIN CHUNG, TÀI CHÍNH & NHÂN VIÊN
        all_orders.append({
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

        # 2. CHI TIẾT SẢN PHẨM
        items = order.get('items', [])
        if isinstance(items, list):
            for item in items:
                v_info = item.get('variation_info', {})
                all_items.append({
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

    df_orders = pd.DataFrame(all_orders)
    df_items = pd.DataFrame(all_items)

    st.title("📊 Hệ thống Trích xuất Dữ liệu Pancake POS")
    st.info(f"Đã tải thành công {len(df_orders)} đơn hàng.") # Hiển thị số đơn đã lấy

    tab1, tab2 = st.tabs(["📑 Đơn hàng & Tài chính", "📦 Chi tiết Sản phẩm & Mã định danh"])

    with tab1:
        st.dataframe(df_orders, use_container_width=True)
    with tab2:
        st.dataframe(df_items, use_container_width=True)
else:
    st.info("Không tìm thấy dữ liệu hoặc lỗi kết nối API.")
