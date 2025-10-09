"""
Cấu hình cho ứng dụng HRM Employee Manager

Chứa các hằng số, tiêu đề cột, URL API và các cài đặt khác.
"""

# URL API
API_URL = "https://hrm.base.vn/extapi/v1/employee/list"

# Cài đặt API
API_PAGE = 1
API_LIMIT = 50

# Ánh xạ tiêu đề cột
HEADERS = {
    'stt': 'STT',
    'id': 'ID',
    'code': 'Mã NV',
    'name': 'Họ tên',
    'email': 'Email',
    'phone': 'Số điện thoại',
    'dob': 'Ngày sinh',
    'position': 'Chức vụ',
    'bank_account': 'Số TK',
    'bank_name': 'Ngân hàng',
    'profile': 'Thông tin cá nhân',
    'bank': 'Chi tiết ngân hàng',
    'form': 'Biểu mẫu',
}

# Cài đặt GUI
GUI_TITLE = "Quản lý nhân viên HRM"
GUI_GEOMETRY = "500x300"
GUI_APPEARANCE = "light"
GUI_THEME = "blue"

# Cài đặt bảng
TABLE_HEIGHT = 800
TABLE_WIDTH = 1400

# Cài đặt tìm kiếm
SEARCH_THRESHOLD = 60  # Ngưỡng fuzzy search

# Cài đặt xuất dữ liệu
EXPORT_FORMATS = ["CSV", "Excel", "JSON"]

# Cài đặt console
CONSOLE_MENU_OPTIONS = {
    '1': 'search',
    '2': 'filter',
    '3': 'sort',
    '4': 'display',
    '5': 'statistics',
    '6': 'export',
    '7': 'reset',
    '8': 'exit'
}