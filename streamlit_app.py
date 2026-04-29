import streamlit as st
import requests
import pandas as pd

# --- THÔNG TIN XÁC THỰC (Theo tài liệu api-1.json) ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def fetch_pancake(endpoint, params=None):
    """Hàm gọi API sử dụng tham số 'api_key' truyền qua Query String"""
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    
    # Tài liệu quy định: name: api_key, in: query
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=15)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Admin", layout="wide")
st.title("📊 Hệ thống Quản trị Pancake POS (Standard API)")

# Kiểm tra trạng thái Key ngay tại Sidebar
if st.sidebar.button("Kiểm tra kết nối API"):
    # Kiểm tra bằng cách lấy thông tin shop: GET /shops/{shop_id}
    res = requests.get(f"{BASE_URL}/shops/{SHOP_ID}", params={"api_key": API_KEY}).json()
    if res.get("success"):
        st.sidebar.success(f"✅ Kết nối thành công Shop: {res['data'].get('name')}")
    else:
        st.sidebar.error("❌ Key không hợp lệ hoặc không có quyền Admin.")

# --- TRUY XUẤT DỮ LIỆU ---
tab1, tab2, tab3 = st.tabs(["📑 Đơn hàng (24/04)", "📥 Nhập hàng", "📈 Tồn kho"])

with tab1:
    st.subheader("Dữ liệu đơn hàng")
    if st.button("Tải đơn hàng ngày 24/04"):
        # Tham số lấy từ tài liệu: inserted_since (YYYY-MM-DD HH:mm:ss)
        params = {
            "inserted_since": "2026-04-24 00:00:00",
            "mode": "all"
        }
        res = fetch_pancake("orders", params)
        if res.get("success") and res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
        else:
            st.info("Trống: Kiểm tra lại quyền của Key hoặc lọc ngày.")

with tab2:
    st.subheader("Phiếu nhập hàng")
    if st.button("Tải danh sách phiếu nhập"):
        # Endpoint từ tài liệu: /shops/{id}/inventory/purchase_orders
        res = fetch_pancake("inventory/purchase_orders")
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
        else:
            st.info("Không có dữ liệu phiếu nhập.")

with tab3:
    st.subheader("Báo cáo tồn kho")
    if st.button("Cập nhật số liệu tồn"):
        # Endpoint từ tài liệu: /shops/{id}/inventory/stats
        res = fetch_pancake("inventory/stats", {"type": "product"})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
