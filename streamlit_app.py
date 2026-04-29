import streamlit as st
import requests
import pandas as pd

# --- THÔNG SỐ ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1/shops"

def get_pancake_data(endpoint, params=None):
    url = f"{BASE_URL}/{SHOP_ID}/{endpoint}"
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    response = requests.get(url, params=query_params)
    return response.json()

st.title("📦 Trình xuất dữ liệu Kho hàng chuẩn")

tab1, tab2 = st.tabs(["🚚 Phiếu Nhập Kho", "📊 Tồn Kho Thực Tế"])

with tab1:
    if st.button("Lấy toàn bộ Phiếu nhập"):
        # GỌI ĐÚNG: /inventory/purchase_orders (Không có /stats)
        res = get_pancake_data("inventory/purchase_orders", {"limit": 50})
        if res.get("success") and res.get("data"):
            df = pd.DataFrame(res["data"])
            st.success(f"Tìm thấy {len(df)} phiếu nhập hàng!")
            st.dataframe(df)
        else:
            st.error("Vẫn không thấy phiếu nhập. Hãy kiểm tra lại API Key.")
            st.write("Phản hồi từ hệ thống:", res)

with tab2:
    if st.button("Xem số lượng tồn"):
        # GỌI ĐÚNG: /inventory/stats?type=variant
        res = get_pancake_data("inventory/stats", {"type": "variant"})
        if res.get("success") and res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
        else:
            st.warning("Bảng tồn kho rỗng.")
