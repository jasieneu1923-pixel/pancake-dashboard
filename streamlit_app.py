import streamlit as st
import requests
import pandas as pd

# --- THÔNG SỐ XÁC THỰC ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake(endpoint, params=None):
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    # Theo tài liệu: api_key truyền qua query string
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    try:
        response = requests.get(url, params=query_params, timeout=15)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

st.title("🚀 Hệ thống Quản trị Dữ liệu Pancake Full")

# TỰ ĐỘNG LẤY DANH SÁCH KHO TRƯỚC
warehouses_res = call_pancake("inventory/warehouses")
warehouse_list = warehouses_res.get("data", [])
warehouse_options = {w['name']: w['id'] for w in warehouse_list} if warehouse_list else {}

tabs = st.tabs(["📑 Đơn hàng", "📦 Phiếu Nhập Kho", "📈 Tồn Kho Thực Tế", "👥 Khách hàng"])

# TAB 1: ĐƠN HÀNG
with tabs[0]:
    if st.button("Lấy đơn hàng 24/04"):
        res = call_pancake("orders", {"inserted_since": "2026-04-24 00:00:00", "mode": "all"})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))

# TAB 2: PHIẾU NHẬP KHO (BỎ /STATS)
with tabs[1]:
    if st.button("Lấy danh sách Phiếu Nhập"):
        # GỌI ĐÚNG: /inventory/purchase_orders (Không có stats ở cuối)
        res = call_pancake("inventory/purchase_orders", {"limit": 50})
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
        else:
            st.warning("Không có dữ liệu phiếu nhập.")

# TAB 3: TỒN KHO (CẦN WAREHOUSE_ID)
with tabs[2]:
    if warehouse_options:
        selected_wh_name = st.selectbox("Chọn kho hàng:", list(warehouse_options.keys()))
        wh_id = warehouse_options[selected_wh_name]
        
        if st.button("Xem tồn kho của kho này"):
            # Truyền cả type và warehouse_id theo tài liệu
            res = call_pancake("inventory/stats", {"type": "variant", "warehouse_id": wh_id})
            if res.get("data"):
                st.dataframe(pd.DataFrame(res["data"]))
            else:
                st.error("Bảng tồn kho rỗng.")
    else:
        st.error("Không tìm thấy ID kho hàng. Hãy kiểm tra lại mục 'Kho hàng' trên POS.")

# TAB 4: KHÁCH HÀNG
with tabs[3]:
    if st.button("Lấy danh sách Khách hàng"):
        res = call_pancake("customers")
        if res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]))
