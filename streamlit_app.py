import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake Advanced Dashboard", layout="wide")

# Sidebar cấu hình
st.sidebar.header("⚙️ BỘ LỌC NÂNG CAO")
password = st.sidebar.text_input("Mật khẩu truy cập", type="password")

if password != "123": 
    st.warning("Vui lòng nhập mật khẩu để xem dữ liệu.")
    st.stop()

# --- THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

@st.cache_data(ttl=300)
def fetch_data():
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/orders"
    params = {"access_token": TOKEN, "limit": 100, "mode": "all"}
    resp = requests.get(url, params=params)
    return resp.json().get("data", []) if resp.status_code == 200 else []

data = fetch_data()

if data:
    df = pd.DataFrame(data)
    
    # --- XỬ LÝ DỮ LIỆU SẢN PHẨM & DANH MỤC ---
    # Bóc tách tên sản phẩm, mã sản phẩm (SKU) và danh mục từ cột 'products'
    def extract_product_info(order_products):
        if not order_products: return [], [], []
        skus = [p.get('sku', '') for p in order_products if p.get('sku')]
        names = [p.get('name', '') for p in order_products if p.get('name')]
        # Giả định danh mục nằm trong thông tin sản phẩm hoặc variation
        categories = [p.get('category_name', 'Chưa phân loại') for p in order_products]
        return skus, names, list(set(categories))

    df['product_skus'], df['product_names'], df['categories'] = zip(*df['products'].apply(extract_product_info))
    
    # Chuẩn hóa thời gian và thông tin khách
    df['inserted_at'] = pd.to_datetime(df['inserted_at'])
    df['customer_name'] = df['customer'].apply(lambda x: x.get('name') if x else 'N/A')
    df['total_price'] = df['total_price'].astype(float)

    # --- GIAO DIỆN BỘ LỌC (SIDEBAR) ---
    st.sidebar.subheader("📦 Lọc theo Sản phẩm")
    
    # 1. Lọc theo Mã sản phẩm (SKU) - Cho phép dán mã vào
    sku_input = st.sidebar.text_input("Dán Mã sản phẩm (SKU) vào đây:")
    
    # 2. Lọc theo Danh mục (Lấy danh sách từ POS)
    all_categories = sorted(list(set([cat for sublist in df['categories'] for cat in sublist])))
    selected_cats = st.sidebar.multiselect("Lọc theo Danh mục:", options=all_categories, default=all_categories)

    # 3. Lọc theo Ngày
    start_date = st.sidebar.date_input("Từ ngày:", df['inserted_at'].min().date())
    end_date = st.sidebar.date_input("Đến ngày:", datetime.now().date())

    # --- LOGIC LỌC THÔNG MINH ---
    def filter_logic(row):
        # Kiểm tra ngày
        date_match = start_date <= row['inserted_at'].date() <= end_date
        # Kiểm tra danh mục
        cat_match = any(cat in selected_cats for cat in row['categories'])
        # Kiểm tra SKU (Nếu có nhập thì mới lọc)
        sku_match = True
        if sku_input:
            sku_match = any(sku_input.lower() in str(s).lower() for s in row['product_skus'])
        
        return date_match and cat_match and sku_match

    df_filtered = df[df.apply(filter_logic, axis=1)]

    # --- HIỂN THỊ KẾT QUẢ ---
    st.title("📊 Dashboard Lọc Đơn Hàng Theo Sản Phẩm")
    
    c1, c2 = st.columns(2)
    c1.metric("Số đơn hàng khớp bộ lọc", len(df_filtered))
    c2.metric("Tổng giá trị đơn hàng", f"{df_filtered['total_price'].sum():,.0f} đ")

    st.subheader("📋 Danh sách đơn hàng chi tiết")
    # Hiển thị bảng kèm cột Mã sản phẩm để đối chiếu
    show_df = df_filtered.copy()
    show_df['Mã SP trong đơn'] = show_df['product_skus'].apply(lambda x: ", ".join(x))
    
    st.dataframe(show_df[[
        'id', 'customer_name', 'Mã SP trong đơn', 'total_price', 'inserted_at'
    ]].rename(columns={
        'customer_name': 'Tên khách', 'total_price': 'Số tiền', 'inserted_at': 'Ngày tạo'
    }), use_container_width=True)

else:
    st.error("Không tìm thấy dữ liệu từ Token của bạn.")
