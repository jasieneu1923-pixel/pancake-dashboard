import streamlit as st
import requests
import pandas as pd

# --- CẤU HÌNH THEO TÀI LIỆU ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake_api(endpoint, params=None):
    """Hàm gọi API dùng chung cho tất cả các bảng"""
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    # Tài liệu quy định tham số bảo mật là 'api_key' truyền qua query
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=15)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full Data", layout="wide")
st.title("🚀 Hệ thống Khai thác Toàn bộ Dữ liệu Pancake POS")

# Tạo các Tab tương ứng với các phân mục trong tài liệu API
tabs = st.tabs([
    "📦 Đơn hàng", 
    "🛒 Sản phẩm", 
    "📥 Nhập hàng", 
    "📉 Tồn kho", 
    "👥 Khách hàng",
    "🏢 Cửa hàng"
])

# 1. BẢNG ĐƠN HÀNG (Orders)
with tabs[0]:
    st.subheader("Danh sách Đơn hàng")
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("Từ ngày", value=pd.to_datetime("2026-04-24"))
    
    if st.button("Lấy dữ liệu Đơn hàng"):
        params = {"inserted_since": f"{date_filter} 00:00:00", "mode": "all"}
        res = call_pancake_api("orders", params)
        if res.get("success") and res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
        else:
            st.warning("Không có dữ liệu đơn hàng.")

# 2. BẢNG SẢN PHẨM (Products)
with tabs[1]:
    st.subheader("Danh mục Sản phẩm")
    if st.button("Lấy danh sách Sản phẩm"):
        res = call_pancake_api("products", {"limit": 100})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)

# 3. BẢNG NHẬP HÀNG (Purchase Orders)
with tabs[2]:
    st.subheader("Phiếu nhập kho")
    if st.button("Lấy phiếu nhập"):
        # Đường dẫn theo tài liệu: inventory/purchase_orders
        res = call_pancake_api("inventory/purchase_orders")
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)

# 4. BẢNG TỒN KHO (Inventory Stats)
with tabs[3]:
    st.subheader("Thống kê Tồn kho")
    st.info("Lấy dữ liệu tồn kho theo biến thể sản phẩm")
    if st.button("Xem tồn kho"):
        res = call_pancake_api("inventory/stats", {"type": "variant"})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)

# 5. BẢNG KHÁCH HÀNG (Customers)
with tabs[4]:
    st.subheader("Danh sách Khách hàng")
    if st.button("Lấy dữ liệu khách"):
        res = call_pancake_api("customers", {"limit": 50})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)

# 6. THÔNG TIN CỬA HÀNG (Shop Info)
with tabs[5]:
    st.subheader("Thông tin Shop & Cấu hình")
    if st.button("Xem thông tin Shop"):
        # Đặc biệt: endpoint lấy thông tin shop chính là GET /shops/{id}
        url = f"{BASE_URL}/shops/{SHOP_ID}"
        res = requests.get(url, params={"api_key": API_KEY}).json()
        if res.get("success"):
            st.json(res["data"])
