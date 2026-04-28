import streamlit as st
import requests
import pandas as pd
from datetime import datetime

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
def fetch_pancake_data(endpoint, extra_params=None):
    url = f"https://pos.pages.fm/api/v1/shops/{SHOP_ID}/{endpoint}"
    params = {"access_token": TOKEN}
    if extra_params: params.update(extra_params)
    try:
        resp = requests.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}
    except: return {}

# --- 3. TẢI DỮ LIỆU ---
# Lấy dữ liệu Đơn hàng (giữ logic cũ)
all_orders_raw = []
pages_to_fetch = 5 
for p in range(1, pages_to_fetch + 1):
    batch = fetch_pancake_data("orders", {"limit": 100, "mode": "all", "page": p})
    page_data = batch.get("data", [])
    if not page_data: break
    all_orders_raw.extend(page_data)

# Lấy dữ liệu mới
purchase_raw = fetch_pancake_data("purchase_orders", {"limit": 50}).get("data", [])
stats_variant_raw = fetch_pancake_data("stats/variants", {"limit": 50}).get("data", [])
stats_product_raw = fetch_pancake_data("stats/products", {"limit": 50}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU ---

# --- BẢNG 1 & 2: GIỮ NGUYÊN Y HỆT CODE GỐC CỦA BẠN ---
all_orders = []
all_items = []

for order in all_orders_raw:
    custom_id = order.get('custom_id')

    # 1. THÔNG TIN CHUNG, TÀI CHÍNH & NHÂN VIÊN
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

    # 2. CHI TIẾT SẢN PHẨM
    items = order.get('items', [])
    if isinstance(items, list):
        for item in items:
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

# --- BẢNG 3: NHẬP HÀNG (DỰA TRÊN JSON MỚI) ---
list_purchase = []
for p in purchase_raw:
    p_id = p.get('display_id')
    for it in p.get('items', []):
        list_purchase.append({
            "Mã phiếu nhập": p_id,
            "Nhà cung cấp": p.get('supplier', {}).get('name'),
            "Sản phẩm": it.get('product_name'),
            "Số lượng": it.get('quantity'),
            "Giá nhập": it.get('imported_price'),
            "Thanh toán trước": p.get('prepaid_debt'),
            "Tiền còn nợ": p.get('total_remain_price'),
            "Ngày nhập": p.get('time_import'),
            "Ghi chú": p.get('note')
        })

# --- BẢNG 4: STATISTICS BY VARIANT ---
list_stats_variant = []
for sv in stats_variant_raw:
    v = sv.get('variation', {})
    fields = v.get('fields') or []
    attr = {f.get('name'): f.get('value') for f in fields}
    list_stats_variant.append({
        "Mã SKU": v.get('custom_id'),
        "Tên sản phẩm": v.get('product', {}).get('name'),
        "Màu": attr.get('Color', ''), "Size": attr.get('Size', ''),
        "Tồn đầu": sv.get('begin_inventory'), "Tổng nhập": sv.get('total_import'),
        "Tổng xuất": sv.get('total_export'), "Tồn cuối": sv.get('end_inventory'),
        "Giá trị tồn cuối": sv.get('end_inventory_value')
    })

# --- BẢNG 5: STATISTICS BY PRODUCT ---
list_stats_product = []
for sp in stats_product_raw:
    p_info = sp.get('product', {})
    list_stats_product.append({
        "Mã SP": p_info.get('custom_id'),
        "Tên sản phẩm": p_info.get('name'),
        "Tồn đầu kỳ": sp.get('begin_inventory'),
        "Nhập từ phiếu": sp.get('purchase_import'),
        "Xuất bán hàng": sp.get('sell_export'),
        "Tồn cuối kỳ": sp.get('end_inventory'),
        "Giá trị tồn cuối": sp.get('end_inventory_value')
    })

# --- 5. HIỂN THỊ ---
st.title("📊 Hệ thống Trích xuất Dữ liệu Pancake POS")
st.info(f"Đã tải thành công {len(all_orders)} đơn hàng.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng & Tài chính", 
    "📦 Sản phẩm trong đơn", 
    "📥 Nhập hàng", 
    "📊 Thống kê Biến thể", 
    "📈 Thống kê Sản phẩm"
])

with tab1: st.dataframe(pd.DataFrame(all_orders), use_container_width=True)
with tab2: st.dataframe(pd.DataFrame(all_items), use_container_width=True)
with tab3: st.dataframe(pd.DataFrame(list_purchase), use_container_width=True)
with tab4: st.dataframe(pd.DataFrame(list_stats_variant), use_container_width=True)
with tab5: st.dataframe(pd.DataFrame(list_stats_product), use_container_width=True)
