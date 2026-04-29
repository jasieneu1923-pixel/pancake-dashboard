import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kiểm tra kết nối Pancake", layout="wide")

# Thử với Key mới nhất bạn vừa tạo ở dòng đầu tiên trong ảnh
TOKEN = "3fd9730696d6408da6df2e9e342f8952" 
SHOP_ID = "30224071"

def fetch_debug(endpoint):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    try:
        r = requests.get(url, params={"access_token": TOKEN}, timeout=10)
        return r.json()
    except:
        return {"error": "Không thể kết nối"}

st.title("🔍 Kiểm tra quyền hạn API")

# Thử lấy danh sách Page trước (Để xem Key này được xem những Page nào)
pages_data = fetch_debug("pages")
# Thử lấy đơn hàng không giới hạn
orders_data = fetch_debug("orders")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Danh sách Page Key được phép xem")
    if "data" in pages_data:
        st.write(f"Key này xem được: {len(pages_data['data'])} Pages")
        st.json(pages_data['data'])
    else:
        st.error("Key này không có quyền xem danh sách Page.")

with col2:
    st.subheader("2. Dữ liệu Đơn hàng thô")
    if "data" in orders_data and orders_data['data']:
        st.success(f"Tìm thấy {len(orders_data['data'])} đơn hàng!")
        st.dataframe(pd.DataFrame(orders_data['data']))
    else:
        st.warning("Danh sách đơn hàng vẫn trống.")
        st.write("Phản hồi từ server:", orders_data)
