import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Pancake ERP Full System", layout="wide")

# Tự động làm mới dữ liệu mỗi 60 giây (Real-time giả lập)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="pancakerefresh")
except:
    pass

# Sidebar bảo mật
st.sidebar.header("⚙️ QUẢN LÝ DỮ LIỆU")
password = st.sidebar.text_input("Mật khẩu", type="password")
if password != "123":
    st.warning("Vui lòng nhập mật khẩu (123) để xem dữ liệu.")
    st.stop()

# --- 2. THÔNG TIN API ---
TOKEN = "2b10f2b9145f4b779e30bd635084f5be"
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
            return resp.json()
        return {}
    except:
        return {}

# --- 3. TẢI DỮ LIỆU ---

# A. Đơn hàng (Lấy dữ liệu từ đầu tháng 4/2026)
all_orders_raw = []
for p in range(1, 4):
    batch = fetch_pancake_data("orders", {
        "limit": 100, 
        "mode": "all", 
        "page": p,
        "inserted_since": "2026-04-01T00:00:00Z"
    })
    data = batch.get("data", [])
    if not data: break
    all_orders_raw.extend(data)

# B. Nhập hàng (Thử nghiệm 2 endpoint để tránh lỗi 404)
# Thử endpoint kho hàng trước, sau đó thử endpoint chung
purchase_res = fetch_pancake_data("inventory/purchase_orders", {"limit": 100})
if not purchase_res.get("data"):
    purchase_res = fetch_pancake_data("purchase_orders", {"limit": 100})
purchase_data = purchase_res.get("data", [])

# C. Thống kê tồn kho
stats_variant_raw = fetch_pancake_data("inventory/stats", {"type": "variant", "limit": 100}).get("data", [])
stats_product_raw = fetch_pancake_data("inventory/stats", {"type": "product", "limit": 100}).get("data", [])

# --- 4. XỬ LÝ DỮ LIỆU (Full Cột) ---

# --- BẢNG 1 & 2: ĐƠN HÀNG ---
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

# --- BẢNG 3: NHẬP HÀNG ---
list_purchase = []
status_map = {-1: "Mới", 0: "Đã xác nhận", 1: "Đã nhập hàng", 2: "Đã hủy"}
for p in purchase_data:
    p_status = status_map.get(p.get('status'), "N/A")
    for it in p.get('items', []):
        list_purchase.append({
            "Mã phiếu": p.get('display_id'),
            "Trạng thái": p_status,
            "Ngày nhập": p.get('time_import') or p.get('inserted_at'),
            "Nhà cung cấp": p.get('supplier', {}).get('name', 'N/A'),
            "Sản phẩm": it.get('product_name'),
            "SL Nhập": it.get('quantity'),
            "Giá nhập": it.get('imported_price'),
            "Chiết khấu SP": it.get('discount'),
            "Tổng SL phiếu": p.get('total_quantity'),
            "Tổng giá trị phiếu": p.get('total_price'),
            "Giảm giá phiếu": p.get('discount'),
            "Phí vận chuyển": p.get('transport_fee'),
            "Trả trước NCC": p.get('prepaid_debt'),
            "Còn nợ": p.get('total_remain_price'),
            "Ghi chú": p.get('note'),
            "Người tạo": p.get('user', {}).get('name')
        })

# --- BẢNG 4 & 5: THỐNG KÊ TỒN KHO ---
list_stats_v = []
for s in stats_variant_raw:
    v = s.get('variation', {})
    p = v.get('product', {})
    list_stats_v.append({
        "Mã mẫu mã": s.get('id'),
        "Tên sản phẩm": p.get('name'),
        "Tên biến thể": v.get('name'),
        "Tồn đầu kỳ": s.get('begin_inventory'),
        "Tổng SL nhập": s.get('total_import'),
        "Tổng SL xuất": s.get('total_export'),
        "Tồn cuối kỳ": s.get('end_inventory'),
        "Giá trị tồn cuối": s.get('end_inventory_value')
    })

list_stats_p = []
for s in stats_product_raw:
    p = s.get('product', {})
    list_stats_p.append({
        "Mã sản phẩm": s.get('id'),
        "Tên sản phẩm": p.get('name'),
        "Tồn đầu": s.get('begin_inventory'),
        "Nhập": s.get('total_import'),
        "Xuất": s.get('total_export'),
        "Tồn cuối": s.get('end_inventory'),
        "Giá trị tồn": s.get('end_inventory_value')
    })

# --- 5. HIỂN THỊ GIAO DIỆN ---
st.title("📊 Hệ thống Quản trị Pancake POS")

# Dashboard Thống kê
if all_orders:
    df_orders = pd.DataFrame(all_orders)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Doanh thu tháng này", f"{df_orders['Tổng tiền (Total Price)'].sum():,.0f}đ")
    col2.metric("Số lượng đơn", len(df_orders))
    col3.metric("Số phiếu nhập kho", len(purchase_data))
    col4.metric("Sản phẩm đang bán", len(list_stats_p))

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Đơn hàng", "📦 SP trong đơn", "📥 Nhập hàng", "📊 Tồn Biến thể", "📈 Tồn Sản phẩm"
])

with tab1:
    st.dataframe(pd.DataFrame(all_orders), use_container_width=True)

with tab2:
    st.dataframe(pd.DataFrame(all_items), use_container_width=True)

with tab3:
    if list_purchase:
        df_p = pd.DataFrame(list_purchase)
        st.dataframe(df_p, use_container_width=True)
        # Biểu đồ phân bổ nhập hàng theo NCC
        fig = px.pie(df_p, names='Nhà cung cấp', values='Giá nhập', title='Tỷ trọng chi phí nhập hàng')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Không lấy được Nhập hàng. Kiểm tra API Key có quyền 'Inventory' không.")

with tab4:
    st.dataframe(pd.DataFrame(list_stats_v), use_container_width=True)

with tab5:
    st.dataframe(pd.DataFrame(list_stats_p), use_container_width=True)
