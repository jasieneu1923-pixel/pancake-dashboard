import streamlit as st
import requests
import pandas as pd

API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def fetch_inventory(path, params=None):
    # Theo tài liệu: /shops/{shop_id}/inventory/...
    url = f"{BASE_URL}/shops/{SHOP_ID}/inventory/{path}"
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    return requests.get(url, params=query_params).json()

st.title("🛠 Kiểm tra chuyên sâu Kho hàng")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Kiểm tra Nhập hàng")
    # Endpoint: /inventory/purchase_orders
    if st.button("Quét phiếu nhập"):
        res = fetch_inventory("purchase_orders")
        if res.get("success") and res.get("data"):
            st.write(f"Tìm thấy {len(res['data'])} phiếu nhập")
            st.dataframe(pd.DataFrame(res['data']))
        else:
            st.error("Không có dữ liệu phiếu nhập.")
            st.write("Phản hồi hệ thống:", res)

with col2:
    st.subheader("2. Kiểm tra Tồn kho (Stats)")
    # Endpoint: /inventory/stats
    if st.button("Quét tồn thực tế"):
        # Tài liệu yêu cầu tham số type: 'product' hoặc 'variant'
        res = fetch_inventory("stats", {"type": "variant"})
        if res.get("success") and res.get("data"):
            st.write(f"Tìm thấy {len(res['data'])} dòng tồn kho")
            st.dataframe(pd.DataFrame(res['data']))
        else:
            st.error("Không có dữ liệu tồn kho.")
            st.json(res)
