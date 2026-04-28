import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP System", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu để xem dữ liệu.")
    st.stop()

# --- 2. THÔNG TIN API ---
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiUGjGsMahbmcgS-G6vyB0b8OhbiBIVCIsImV4cCI6MTc4NDYyMzUwNCwiYXBwbGljYXRpb24iOjEsInVpZCI6ImE5OTExMjE4LWUzNGYtNDg1Mi1hYWE1LThlNDk4MTUzZjNkMyIsInNlc3Npb25faWQiOiJlYTBhODUyMy0zMmY2LTQ4MTktOGM3OC1iYjRlY2MzMTMyZTgiLCJpYXQiOjE3NzY4NDc1MDQsImZiX2lkIjoiMTIwMzAwMTc0NDgwODYzIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IlBoxrDGoW5nIEvhur8gdG_DoW4gSFQifQ.LSw3FdrrNAzBrEYD5IwKPNY6jjvdH3_m9UEtcalFwR4"
SHOP_ID = "30224071"

@st.cache_data(ttl=60)
def fetch_pancake_data(endpoint, params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    base_params = {"access_token": TOKEN}
    if params:
        base_params.update(params)
    try:
        resp = requests.get(url, params=base_params)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        return []
    except:
        return []

# --- 3. TẢI DỮ LIỆU ---

# A. Lấy Đơn hàng (Giữ nguyên logic cũ của bạn)
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    if not batch: break
    all_orders_raw.extend(batch)

# B. Lấy danh sách Sản phẩm (Mục "Sản phẩm" trong ảnh)
products_raw = fetch_pancake_data("products", {"limit": 100, "is_removed": False})

# C. Lấy phiếu Nhập hàng (Mục "Nhập hàng" trong ảnh)
purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 100})

# --- 4. XỬ LÝ DỮ LIỆU ---

# --- BẢNG 1 & 2: GIỮ NGUYÊN 100% CẤU TRÚC BẠN YÊU CẦU ---
all_orders = []
all_items = []

for order in all_orders_raw:
    custom_id = order.get('custom_id')
    all_orders.append({
        "Mã tùy chỉnh (Custom ID)": custom_id,
        "Tên Page": order.get('page', {}).get('name'),
        "Trạng thái (Số)": order.get('status'),
        "Ngày tạo": order.get('inserted_at'),
        "Tên khách": order.get('bill_full_name'),
        "SĐT khách": order.get('bill_phone_number'),
        "Nhân viên tạo": order.get('creator', {}).get('name'),
        "Tổng tiền (Total Price)": order.get('total_price'),
        "Tiền thu hộ (COD)": order.get('cod'),
        "Phí ship báo khách": order.get('shipping_fee'),
        "Tiền chuyển khoản": order.get('transfer_money'),
        "Tiền mặt": order.get('cash')
    })
    
    for item in order.get('items', []):
        v_info = item.get('variation_info', {})
        all_items.append({
            "Mã đơn (Custom ID)": custom_id,
            "Tên sản phẩm": v_info.get('name'),
            "Chi tiết": v_info.get('detail'),
            "Mã SKU": v_info.get('id'),
            "Số lượng": item.get('quantity'),
            "Giá bán niêm yết": v_info.get('retail_price'),
            "Giá nhập cuối": v_info.get('last_imported_price'),
            "Tên Kho": order.get('warehouse_info', {}).get('name')
        })

# --- BẢNG 3: DANH MỤC SẢN PHẨM (Mục bạn khoanh đỏ) ---
list_products = []
for p in products_raw:
    # Lấy thông tin các biến thể (size, màu) nếu có
    variations = p.get('variations', [])
    for v in variations:
        list_products.append({
            "Mã SP (ID)": p.get('id'),
            "Tên sản phẩm": p.get('name'),
            "Mã SKU": v.get('custom_id'),
            "Tên biến thể": v.get('name'),
            "Giá bán": v.get('retail_price'),
            "Giá nhập": v.get('last_imported_price'),
            "Tồn kho hiện tại": v.get('inventory_number'),
            "Đã xóa": "Rồi" if v.get('is_removed') else "Chưa"
        })

# --- BẢNG 4: DANH SÁCH NHẬP HÀNG (Mục bạn khoanh đỏ) ---
list_purchase = []
for po in purchase_raw:
    po_items = po.get('items', [])
    for it in po_items:
        list_purchase.append({
            "Mã phiếu nhập": po.get('display_id'),
            "Ngày nhập": po.get('time_import'),
            "Nhà cung cấp": po.get('supplier', {}).get('name', 'Không xác định'),
            "Tên sản phẩm nhập": it.get('product_name'),
            "Số lượng": it.get('quantity'),
            "Giá nhập": it.get('imported_price'),
            "Thành tiền sản phẩm": it.get('total_price'),
            "Tổng tiền phiếu": po.get('total_price'),
            "Trạng thái thanh toán": "Đã trả đủ" if po.get('total_remain_price') == 0 else f"Còn nợ {po.get('total_remain_price')}",
            "Người thực hiện": po.get('user', {}).get('name')
        })

# --- 5. HIỂN THỊ ---
st.title("🚀 Pancake POS Data Analytics")

tabs = st.tabs(["📑 Đơn hàng", "📦 SP trong đơn", "🍎 Danh mục Sản phẩm", "📥 Phiếu Nhập hàng"])

with tabs[0]:
    st.dataframe(pd.DataFrame(all_orders), use_container_width=True)
with tabs[1]:
    st.dataframe(pd.DataFrame(all_items), use_container_width=True)
with tabs[2]:
    if list_products:
        st.dataframe(pd.DataFrame(list_products), use_container_width=True)
    else:
        st.info("Không có dữ liệu Sản phẩm hoặc Token không có quyền xem mục này.")
with tabs[3]:
    if list_purchase:
        st.dataframe(pd.DataFrame(list_purchase), use_container_width=True)
    else:
        st.info("Không có dữ liệu Nhập hàng. Hãy kiểm tra lại các phiếu nhập trong POS.")
