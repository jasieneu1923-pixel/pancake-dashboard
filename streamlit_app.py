import streamlit as st
import requests
import pandas as pd

# --- THÔNG SỐ ---
API_KEY = "faea6078b156431fa19f7ac903dda137"
SHOP_ID = "30224071"
BASE_URL = "https://pos.pages.fm/api/v1"

def fetch_full_products():
    url = f"{BASE_URL}/shops/{SHOP_ID}/products"
    # Thêm limit cao để lấy hết sản phẩm
    params = {"api_key": API_KEY, "limit": 100}
    
    try:
        response = requests.get(url, params=params, timeout=20)
        res_json = response.json()
        
        if res_json.get("success") and res_json.get("data"):
            raw_products = res_json["data"]
            all_rows = []
            
            # Duyệt qua từng sản phẩm để bóc tách toàn bộ trường dữ liệu
            for p in raw_products:
                # Nếu sản phẩm có nhiều biến thể (màu, size)
                variants = p.get("variations", [])
                if variants:
                    for v in variants:
                        row = {
                            "ID Sản phẩm": p.get("id"),
                            "Tên sản phẩm": p.get("name"),
                            "Danh mục": p.get("category_id"),
                            "ID Biến thể": v.get("id"),
                            "Tên biến thể": v.get("name"),
                            "Mã SKU": v.get("sku"),
                            "Giá bán lẻ": v.get("retail_price"),
                            "Giá nhập": v.get("import_price"),
                            "Giá sỉ": v.get("wholesale_price"),
                            "Khối lượng (g)": v.get("weight"),
                            "Quản lý kho": "Bật" if v.get("is_inventory") else "Tắt",
                            "Mô tả": p.get("description"),
                            "Ngày tạo": p.get("inserted_at")
                        }
                        all_rows.append(row)
                else:
                    # Nếu sản phẩm không có biến thể
                    all_rows.append({
                        "ID Sản phẩm": p.get("id"),
                        "Tên sản phẩm": p.get("name"),
                        "Danh mục": p.get("category_id"),
                        "Mã SKU": p.get("sku"),
                        "Giá bán lẻ": p.get("retail_price"),
                        "Mô tả": p.get("description"),
                        "Ngày tạo": p.get("inserted_at")
                    })
            return all_rows
        return []
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return []

st.title("📦 Toàn bộ danh mục Sản phẩm & Biến thể")

if st.button("Tải dữ liệu đầy đủ"):
    with st.spinner("Đang bóc tách dữ liệu..."):
        full_data = fetch_full_products()
        if full_data:
            df = pd.DataFrame(full_data)
            st.success(f"Đã mở rộng thành công {len(df)} dòng dữ liệu!")
            
            # Hiển thị bảng dữ liệu đầy đủ
            st.dataframe(df, use_container_width=True)
            
            # Nút tải file Excel
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Tải file CSV đầy đủ", csv, "pancake_products_full.csv", "text/csv")
        else:
            st.warning("Không lấy được dữ liệu hoặc danh sách rỗng.")
