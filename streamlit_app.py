import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Cấu hình giao diện
st.set_page_config(page_title="Pancake POS Dashboard", layout="wide")
st.title("📊 Hệ Thống Quản Lý Đơn Hàng Pancake")

# Thông tin cấu hình (Sử dụng Token của bạn)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

STATUS_MAP = {
    "0": "Mới", "1": "Đã xác nhận", "2": "Đã gửi hàng", "3": "Đã nhận",
    "8": "Đang đóng gói", "12": "Chờ in", "13": "Đã in", "5": "Đã hoàn"
}

# Hàm lấy dữ liệu trực tiếp từ API
def get_pancake_orders(limit=100):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/orders"
    params = {"access_token": TOKEN, "limit": limit}
    resp = requests.get(url, params=params)
    return resp.json().get("data", []) if resp.status_code == 200 else []

# Giao diện chính
data = get_pancake_orders()

if data:
    df = pd.DataFrame(data)
    df['status_vn'] = df['status'].astype(str).map(STATUS_MAP).fillna("Khác")
    df['total_price'] = df['total_price'].astype(float)
    
    # Hiển thị chỉ số nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng đơn (100 đơn gần nhất)", len(df))
    c2.metric("Doanh thu tạm tính", f"{df['total_price'].sum():,.0f} đ")
    c3.metric("Số đơn đã xác nhận", len(df[df['status'] == 1])) # Logic trạng thái

    # Biểu đồ trạng thái đơn hàng
    st.subheader("Phân tích trạng thái đơn hàng")
    fig = px.bar(df['status_vn'].value_counts().reset_index(), x='status_vn', y='count', color='status_vn')
    st.plotly_chart(fig, use_container_width=True)

    # Bảng dữ liệu chi tiết
    st.subheader("Danh sách đơn hàng chi tiết")
    st.dataframe(df[['id', 'inserted_at', 'status_vn', 'total_price']])
else:
    st.warning("Đang chờ dữ liệu hoặc Token hết hạn.")