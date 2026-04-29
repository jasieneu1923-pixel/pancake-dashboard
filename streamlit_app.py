import streamlit as st
import requests
import pandas as pd

# Thông tin từ tài liệu và ảnh của bạn
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_api(endpoint, params=None):
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    # Tài liệu quy định dùng tham số 'api_key' trong Query String
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=15)
        return response.json()
    except:
        return {"success": False, "message": "Lỗi kết nối"}

st.title("🚀 Pancake Data Explorer (API Key Only)")

# Các bảng dữ liệu chính trong tài liệu
tabs = st.tabs(["📦 Đơn hàng", "📈 Tồn kho", "📥 Nhập hàng", "👥 Khách hàng"])

# BẢNG ĐƠN HÀNG
with tabs[0]:
    if st.button("Quét Đơn hàng 24/04"):
        res = call_api("orders", {"inserted_since": "2026-04-24 00:00:00", "mode": "all"})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
        else:
            st.warning("Dữ liệu đơn hàng trống.")

# BẢNG TỒN KHO (Lý do hay bị rỗng nằm ở đây)
with tabs[1]:
    st.info("Lưu ý: Phải có tham số 'type' thì API mới trả dữ liệu tồn.")
    if st.button("Quét Tồn kho thực tế"):
        # QUAN TRỌNG: Tài liệu yêu cầu type là 'product' hoặc 'variant'
        res = call_api("inventory/stats", {"type": "variant"})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
        else:
            st.error("Bảng tồn kho rỗng. Phản hồi: " + str(res))

# BẢNG NHẬP HÀNG
with tabs[2]:
    if st.button("Quét Phiếu nhập"):
        res = call_api("inventory/purchase_orders")
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
        else:
            st.warning("Chưa có phiếu nhập hàng nào.")

# BẢNG KHÁCH HÀNG
with tabs[3]:
    if st.button("Quét Khách hàng"):
        res = call_api("customers")
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
