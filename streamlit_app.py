import streamlit as st
import requests
import pandas as pd

API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def force_fetch_purchase_orders():
    url = f"{BASE_URL}/shops/{SHOP_ID}/inventory/purchase_orders"
    
    # Thử quét với nhiều tham số khác nhau theo tài liệu
    # 1. Thử lấy 100 phiếu gần nhất
    # 2. Thử mode 'all' để lấy cả phiếu nháp và hoàn thành
    params = {
        "api_key": API_KEY,
        "limit": 100,
        "mode": "all" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

st.title("🔍 Truy quét sâu Phiếu Nhập Kho")

if st.button("Bắt đầu quét toàn bộ phiếu nhập"):
    res = force_fetch_purchase_orders()
    
    if res.get("success") and res.get("data"):
        st.success(f"Đã tìm thấy {len(res['data'])} phiếu nhập kho!")
        df = pd.DataFrame(res["data"])
        st.dataframe(df)
    else:
        st.error("Kết quả vẫn trả về rỗng.")
        st.info("Phân tích kỹ thuật:")
        st.json(res) # Xem chi tiết lỗi hệ thống trả về
