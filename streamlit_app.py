import streamlit as st
import requests
import pandas as pd

# --- 1. THÔNG TIN XÁC THỰC (Lấy từ tài liệu api-1.json) ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake_api(endpoint, params=None):
    """Hàm gọi API đúng chuẩn paths trong tài liệu"""
    # Cấu trúc: /shops/{shop_id}/{endpoint}
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    
    # Tài liệu mục securitySchemes quy định tham số là 'api_key' nằm ở 'query'
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=15)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- 2. GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Pancake Standard API", layout="wide")
st.title("📊 Hệ thống Báo cáo Pancake POS (Chuẩn API)")

tab1, tab2, tab3 = st.tabs(["📑 Đơn hàng (24/04)", "📥 Nhập hàng", "📈 Tồn kho"])

with tab1:
    st.subheader("Truy xuất Đơn hàng (Endpoint: /orders)")
    # Theo tài liệu, sử dụng 'inserted_since' để lọc thời gian
    if st.button("Tải dữ liệu đơn hàng 24/04"):
        params = {
            "inserted_since": "2026-04-24 00:00:00",
            "mode": "all" # Lấy tất cả trạng thái
        }
        res = call_pancake_api("orders", params)
        
        if res.get("success") and res.get("data"):
            orders = res["data"]
            # Chuyển đổi thành bảng dễ nhìn
            df_orders = pd.DataFrame([{
                "Mã đơn": o.get('custom_id'),
                "Khách hàng": o.get('bill_full_name'),
                "SĐT": o.get('bill_phone_number'),
                "Tổng tiền": o.get('total_price'),
                "Ngày tạo": o.get('inserted_at'),
                "Trạng thái": o.get('status')
            } for o in orders])
            st.success(f"Tìm thấy {len(df_orders)} đơn hàng.")
            st.dataframe(df_orders, use_container_width=True)
        else:
            st.warning("Không có dữ liệu hoặc API Key chưa được cấp quyền 'Orders'.")
            if not res.get("success"): st.error(f"Chi tiết lỗi: {res}")

with tab2:
    st.subheader("Phiếu nhập kho (Endpoint: /inventory/purchase_orders)")
    if st.button("Tải danh sách nhập hàng"):
        res = call_pancake_api("inventory/purchase_orders")
        if res.get("success") and res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
        else:
            st.info("Trống: Không có phiếu nhập hàng.")

with tab3:
    st.subheader("Thống kê tồn kho (Endpoint: /inventory/stats)")
    if st.button("Cập nhật tồn kho"):
        # Theo tài liệu tham số 'type' có thể là 'product' hoặc 'variant'
        res = call_pancake_api("inventory/stats", {"type": "product"})
        if res.get("success") and res.get("data"):
            st.dataframe(pd.DataFrame(res["data"]), use_container_width=True)
        else:
            st.info("Không lấy được dữ liệu tồn kho.")

# --- KIỂM TRA QUYỀN ADMIN ---
st.sidebar.markdown("---")
if st.sidebar.button("Kiểm tra quyền của API Key"):
    # Kiểm tra endpoint cơ bản nhất: /shops/{shop_id}
    shop_res = requests.get(f"{BASE_URL}/shops/{SHOP_ID}", params={"api_key": API_KEY}).json()
    if shop_res.get("success"):
        st.sidebar.success(f"✅ Kết nối OK: {shop_res['data'].get('name')}")
    else:
        st.sidebar.error("❌ Key không hợp lệ hoặc thiếu quyền.")
