import streamlit as st
import requests
import pandas as pd
import time

# --- THÔNG SỐ XÁC THỰC ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def call_pancake_all_pages(endpoint, params=None):
    """Hàm tự động quét qua tất cả các trang dữ liệu từ trước đến nay"""
    all_data = []
    page = 1
    if params is None: params = {}
    
    # Thiết lập giới hạn mỗi trang cao nhất có thể (thường là 100)
    params.update({"api_key": API_KEY, "limit": 100})
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    while True:
        status_text.text(f" đang quét trang {page} của mục {endpoint}...")
        params["page"] = page
        
        try:
            url = f"{BASE_URL}/shops/{SHOP_ID}/{endpoint}"
            response = requests.get(url, params=params, timeout=20).json()
            
            if response.get("success") and response.get("data"):
                current_batch = response["data"]
                all_data.extend(current_batch)
                
                # Nếu số lượng trả về ít hơn giới hạn (limit), nghĩa là đã hết dữ liệu
                if len(current_batch) < 100:
                    break
                page += 1
                time.sleep(0.2) # Nghỉ ngắn để tránh bị chặn (Rate Limit)
            else:
                break
        except Exception as e:
            st.error(f"Lỗi tại trang {page}: {e}")
            break
            
    progress_bar.empty()
    status_text.empty()
    return all_data

# --- GIAO DIỆN ---
st.set_page_config(page_title="Pancake Lifetime Data", layout="wide")
st.title("🗄️ Hệ thống Trích xuất Toàn bộ Lịch sử Shop")

menu = {
    "📑 Tất cả Đơn hàng (Lifetime)": "orders",
    "📦 Tất cả Phiếu nhập kho": "inventory/purchase_orders",
    "🛒 Toàn bộ Danh mục Sản phẩm": "products",
    "👥 Toàn bộ Danh sách Khách hàng": "customers"
}

selection = st.selectbox("Chọn bảng dữ liệu muốn quét từ đầu:", list(menu.keys()))

if st.button(f"Bắt đầu quét toàn bộ dữ liệu"):
    endpoint = menu[selection]
    
    # Riêng với Đơn hàng, bỏ tham số thời gian để lấy từ đầu
    fetch_params = {}
    if endpoint == "orders":
        fetch_params = {"mode": "all"} # Lấy mọi trạng thái đơn
    
    with st.spinner("Hệ thống đang quét dữ liệu lịch sử..."):
        data = call_pancake_all_pages(endpoint, fetch_params)
        
        if data:
            df = pd.DataFrame(data)
            st.success(f"✅ Hoàn tất! Đã lấy được tổng cộng {len(df)} dòng dữ liệu.")
            
            # Mở rộng bảng nếu là Sản phẩm (để lấy giá nhập/biến thể)
            if endpoint == "products":
                st.info("Đang bóc tách chi tiết biến thể và giá nhập...")
                expanded_rows = []
                for p in data:
                    for v in p.get("variations", []):
                        v.update({"product_name": p.get("name"), "category_id": p.get("category_id")})
                        expanded_rows.append(v)
                df = pd.DataFrame(expanded_rows)

            st.dataframe(df, use_container_width=True)
            
            # Xuất file
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Tải về toàn bộ dữ liệu (.csv)", csv, f"full_history_{endpoint.replace('/','_')}.csv", "text/csv")
        else:
            st.warning("Không tìm thấy dữ liệu nào trong mục này.")
