import streamlit as st
import requests
import pandas as pd

# --- THÔNG SỐ XÁC THỰC ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake(endpoint, params=None):
    """Hàm gọi API bám sát tài liệu api-1.json"""
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=15)
        # Nếu gặp lỗi 403 như trong ảnh bạn gửi
        if response.status_code == 403:
            return {"success": False, "error_type": "FORBIDDEN", "message": "API Key không có quyền truy cập bảng này. Hãy kiểm tra cài đặt nhân viên hoặc phân quyền App."}
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

st.title("🚀 Pancake ERP - Toàn bộ bảng dữ liệu")

# Định nghĩa các bảng từ tài liệu
tables = {
    "📑 Đơn hàng": ("orders", {"mode": "all", "inserted_since": "2026-04-24 00:00:00"}),
    "📦 Phiếu Nhập": ("inventory/purchase_orders", {}),
    "📈 Tồn Kho": ("inventory/stats", {"type": "variant"}),
    "🛒 Sản phẩm": ("products", {}),
    "👥 Khách hàng": ("customers", {}),
    "🏢 Kho hàng": ("inventory/warehouses", {})
}

tab_objs = st.tabs(list(tables.keys()))

for i, (label, (endpoint, default_params)) in enumerate(tables.items()):
    with tab_objs[i]:
        st.subheader(f"Dữ liệu bảng {label}")
        if st.button(f"Tải {label}", key=f"btn_{endpoint}"):
            res = call_pancake(endpoint, default_params)
            
            if res.get("success") and res.get("data"):
                df = pd.DataFrame(res["data"])
                st.success(f"Thành công! Tìm thấy {len(df)} dòng.")
                st.dataframe(df, use_container_width=True)
            else:
                st.error(res.get("message", "Dữ liệu trống hoặc lỗi quyền truy cập."))
                if res.get("error_type") == "FORBIDDEN":
                    st.info("💡 Cách xử lý: Bạn hãy vào Cấu hình -> Nhân viên -> Tìm tài khoản của bạn -> Tích chọn 'Quyền API/Webhook cho Kho hàng'.")
                st.json(res)
