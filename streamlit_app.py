import streamlit as st
import requests
import pandas as pd

# --- CẤU HÌNH THEO TÀI LIỆU API ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake(endpoint, params=None):
    """Hàm gọi API chuẩn theo cấu trúc paths trong tài liệu"""
    url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
    # Tài liệu quy định tham số bảo mật là 'api_key' nằm ở 'query'
    query_params = {"api_key": API_KEY}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=20)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Pancake Data Center", layout="wide")
st.title("🛡️ Hệ thống Khai thác Dữ liệu Pancake POS")

# Danh sách các bảng (Endpoints) có trong tài liệu api-1.json
menu = {
    "📑 Đơn hàng": "orders",
    "🛒 Sản phẩm": "products",
    "📉 Tồn kho": "inventory/stats",
    "📥 Nhập hàng": "inventory/purchase_orders",
    "👥 Khách hàng": "customers",
    "🏷️ Danh mục": "categories"
}

tab_list = st.tabs(list(menu.keys()))

for i, (label, endpoint) in enumerate(menu.items()):
    with tab_list[i]:
        st.subheader(f"Dữ liệu từ bảng: {label}")
        
        # Cấu hình riêng cho từng loại dữ liệu
        params = {}
        if endpoint == "orders":
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Lấy đơn từ ngày", value=pd.to_datetime("2026-04-24"), key=f"date_{endpoint}")
                params = {"inserted_since": f"{date} 00:00:00", "mode": "all"}
        
        if endpoint == "inventory/stats":
            params = {"type": "variant"} # Lấy tồn kho chi tiết theo màu/size
            
        if st.button(f"Tải dữ liệu {label}", key=f"btn_{endpoint}"):
            with st.spinner("Đang truy xuất..."):
                res = call_pancake(endpoint, params)
                
                if res.get("success") or "data" in res:
                    data = res.get("data", [])
                    if data:
                        df = pd.DataFrame(data)
                        st.success(f"Đã lấy thành công {len(df)} dòng dữ liệu.")
                        st.dataframe(df, use_container_width=True)
                        
                        # Cho phép tải về file Excel/CSV
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Tải file CSV", csv, f"{endpoint}.csv", "text/csv")
                    else:
                        st.warning("Bảng này hiện tại chưa có dữ liệu.")
                else:
                    st.error(f"Lỗi API: {res.get('message', 'Không rõ nguyên nhân')}")
                    st.info("Mẹo: Kiểm tra lại xem API Key đã được tích quyền cho bảng này chưa.")

# --- KIỂM TRA THÔNG TIN SHOP ---
st.sidebar.header("Cửa hàng hiện tại")
if st.sidebar.button("Xem thông tin Shop"):
    # Theo tài liệu: GET /shops/{id}
    shop_res = requests.get(f"{BASE_URL}/shops/{SHOP_ID}", params={"api_key": API_KEY}).json()
    if shop_res.get("success"):
        st.sidebar.json(shop_res["data"])
    else:
        st.sidebar.error("Không thể lấy thông tin Shop.")
