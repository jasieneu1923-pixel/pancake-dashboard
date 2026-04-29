import streamlit as st
import requests
import pandas as pd

# --- THÔNG SỐ XÁC THỰC ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def fetch_all_product_fields():
    url = f"{BASE_URL}/shops/{SHOP_ID}/products"
    params = {"api_key": API_KEY, "limit": 100}
    
    try:
        response = requests.get(url, params=params, timeout=20)
        res_json = response.json()
        
        if res_json.get("success") and res_json.get("data"):
            raw_products = res_json["data"]
            all_rows = []
            
            for p in raw_products:
                # Lấy thông tin biến thể (nếu có)
                variants = p.get("variations", [])
                
                # Nếu không có biến thể, tạo 1 dòng giả định để lấy thông tin sản phẩm cha
                if not variants:
                    variants = [{}] 

                for v in variants:
                    row = {
                        # --- THÔNG TIN SẢN PHẨM (PRODUCT) ---
                        "Product ID": p.get("id"),
                        "Tên Sản Phẩm": p.get("name"),
                        "Mô tả": p.get("description"),
                        "Loại Sản Phẩm": p.get("type"),
                        "Danh Mục ID": p.get("category_id"),
                        "Thương Hiệu ID": p.get("brand_id"),
                        "Ngày Tạo": p.get("inserted_at"),
                        "Ngày Cập Nhật": p.get("updated_at"),
                        "Trạng Thái": "Đang bán" if p.get("is_published") else "Ngừng bán",
                        
                        # --- THÔNG TIN BIẾN THỂ (VARIATION) ---
                        "Variation ID": v.get("id"),
                        "Tên Biến Thể": v.get("name"),
                        "Mã SKU": v.get("sku"),
                        "Mã Vạch (Barcode)": v.get("barcode"),
                        
                        # --- GIÁ CẢ (PRICING) ---
                        "Giá Bán Lẻ": v.get("retail_price"),
                        "Giá Nhập": v.get("import_price"),
                        "Giá Sỉ": v.get("wholesale_price"),
                        "Giá Niêm Yết": v.get("original_price"),
                        
                        # --- KHO HÀNG & VẬN CHUYỂN ---
                        "Quản Lý Kho": v.get("is_inventory"),
                        "Khối Lượng (gram)": v.get("weight"),
                        "Đơn Vị Tính": v.get("unit"),
                        "Chiều Dài": v.get("length"),
                        "Chiều Rộng": v.get("width"),
                        "Chiều Cao": v.get("height"),
                        
                        # --- THUỘC TÍNH CHI TIẾT ---
                        "Thuộc Tính 1": v.get("option1"),
                        "Thuộc Tính 2": v.get("option2"),
                        "Thuộc Tính 3": v.get("option3"),
                        "Ảnh Đại Diện": v.get("image") or p.get("images", [None])[0]
                    }
                    all_rows.append(row)
            return all_rows
        return []
    except Exception as e:
        st.error(f"Lỗi truy xuất: {e}")
        return []

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Pancake Product Master Data", layout="wide")
st.title("📦 Toàn bộ thuộc tính sản phẩm (Full Fields)")

if st.button("🚀 Trích xuất toàn bộ dữ liệu sản phẩm"):
    with st.spinner("Đang xử lý dữ liệu..."):
        data = fetch_all_product_fields()
        if data:
            df = pd.DataFrame(data)
            
            # Thống kê nhanh
            st.success(f"Đã lấy thành công {len(df)} dòng (bao gồm cả biến thể).")
            
            # Hiển thị bảng
            st.dataframe(df, use_container_width=True)
            
            # Xuất dữ liệu
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải về file CSV", csv, "full_products.csv", "text/csv")
            with col2:
                st.info("Mẹo: Dữ liệu đã bao gồm đầy đủ Giá nhập, SKU và các thông tin vận chuyển.")
        else:
            st.warning("Không tìm thấy dữ liệu. Hãy kiểm tra lại API Key và Shop ID.")
