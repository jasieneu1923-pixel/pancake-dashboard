import streamlit as st
import requests
import pandas as pd

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
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
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

# --- 3. TẢI DỮ LIỆU ĐA LUỒNG ---

# A. Đơn hàng (Giữ nguyên logic của bạn)
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    data = batch.get("data", [])
    if not data: break
    all_orders_raw.extend(data)

# B. Nhập hàng (Cập nhật endpoint chuẩn)
purchase_data = fetch_pancake_data("purchase_orders", {"limit": 50}).get("data", [])

# C. Thống kê (Sử dụng endpoint inventory/reports)
# Lưu ý: Thường Pancake dùng tham số 'mode' hoặc 'type' để phân loại report
stats_variant_data = fetch_pancake_data("inventory/reports", {"mode": "variant", "limit": 100}).get("data", [])
stats_product_data = fetch_pancake_data("inventory/reports", {"mode": "product", "limit": 100}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# --- BẢNG 1 & 2: GIỮ NGUYÊN 100% NHƯ YÊU CẦU ---
all_orders, all_items = [], []
for order in all_orders_raw:
    custom_id = order.get('custom_id')
    all_orders.append({
        "Mã tùy chỉnh (Custom ID)": custom_id,
        "Tên Page": order.get('page', {}).get('name'),
        "Page ID": order.get('page_id'),
        "Trạng thái (Số)": order.get('status'),
        "Ngày tạo": order.get('inserted_at'),
        "Ngày cập nhật": order.get('updated_at'),
        "Tên khách": order.get('bill_full_name'),
        "SĐT khách": order.get('bill_phone_number'),
        "Nhân viên tạo": order.get('creator', {}).get('name'),
        "Nhân viên cập nhật cuối": order.get('updator', {}).get('name'),
        "Tổng tiền (Total Price)": order.get('total_price'),
        "Tiền thu hộ (COD)": order.get('cod'),
        "Giảm giá đơn (Discount)": order.get('discount'),
        "Tổng giảm giá (Total Discount)": order.get('total_discount'),
        "Phí ship báo khách (Shipping Fee)": order.get('shipping_fee'),
        "Khách trả phí (Customer Pay Fee)": order.get('customer_pay_fee'),
        "Tiền chuyển khoản": order.get('transfer_money'),
        "Tiền mặt": order.get('cash'),
        "Nguồn Ads": order.get('ads_source')
    })
    for item in order.get('items', []):
        v_info = item.get('variation_info', {})
        all_items.append({
            "Mã đơn (Custom ID)": custom_id,
            "Tên sản phẩm": v_info.get('name'),
            "Chi tiết": v_info.get('detail'),
            "Mã SKU (Var ID)": v_info.get('id'),
            "Mã SP Gốc (Prod ID)": v_info.get('product_id'),
            "Số lượng": item.get('quantity'),
            "Giá bán niêm yết": v_info.get('retail_price'),
            "Giá nhập cuối": v_info.get('last_imported_price'),
            "Tên Kho": order.get('warehouse_info', {}).get('name')
        })

# --- BẢNG 3: NHẬP HÀNG (Lọc dữ liệu linh hoạt) ---
list_purchase = []
for p in purchase_data:
    for it in p.get('items', []):
        list_purchase.append({
            "Mã phiếu": p.get('display_id'),
            "Ngày nhập": p.get('time_import') or p.get('inserted_at'),
            "Nhà cung cấp": p.get('supplier', {}).get('name', 'N/A'),
            "Sản phẩm": it.get('product_name'),
            "SL": it.get('quantity'),
            "Giá nhập": it.get('imported_price'),
            "Tổng tiền phiếu": p.get('total_price'),
            "Còn nợ": p.get('total_remain_price')
        })

# --- BẢNG 4 & 5: THỐNG KÊ (Hỗ trợ cả 2 cấu trúc JSON bạn gửi) ---
def process_stats(data_raw):
    processed = []
    for s in data_raw:
        v = s.get('variation', {})
        p = s.get('product', p_info := s.get('product', {})) # Thử lấy từ nhiều nguồn
        processed.append({
            "Tên sản phẩm": p.get('name') or v.get('product', {}).get('name'),
            "Mã hiển thị": v.get('display_id') or p.get('display_id'),
            "Tồn đầu": s.get('begin_inventory'),
            "Tổng nhập": s.get('total_import'),
            "Tổng xuất": s.get('total_export'),
            "Tồn cuối": s.get('end_inventory'),
            "Giá trị tồn cuối": s.get('end_inventory_value')
        })
    return processed

list_stats_v = process_stats(stats_variant_data)
list_stats_p = process_stats(stats_product_data)

# --- 5. HIỂN THỊ ---
st.title("📊 Hệ thống Quản trị Pancake POS")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📑 Đơn hàng", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Thống kê Biến thể", "📈 Thống kê Sản phẩm"])

with tab1: st.dataframe(pd.DataFrame(all_orders), use_container_width=True)
with tab2: st.dataframe(pd.DataFrame(all_items), use_container_width=True)
with tab3:
    if list_purchase: st.dataframe(pd.DataFrame(list_purchase), use_container_width=True)
    else: st.info("Chưa có dữ liệu Nhập hàng hoặc Token không đủ quyền truy cập mục 'Nhập hàng'.")
with tab4:
    if list_stats_v: st.dataframe(pd.DataFrame(list_stats_v), use_container_width=True)
    else: st.info("Không tìm thấy dữ liệu thống kê biến thể.")
with tab5:
    if list_stats_p: st.dataframe(pd.DataFrame(list_stats_p), use_container_width=True)
    else: st.info("Không tìm thấy dữ liệu thống kê sản phẩm.")
