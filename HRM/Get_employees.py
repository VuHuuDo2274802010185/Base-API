"""
Ứng dụng Quản lý Nhân viên HRM

Module này cung cấp một công cụ toàn diện để lấy, hiển thị, tìm kiếm,
lọc và xuất dữ liệu nhân viên từ HRM Base API.

Tính năng:
- Giao diện GUI sử dụng CustomTkinter để quản lý nhân viên tương tác
- Chế độ console để vận hành dòng lệnh
- Tìm kiếm fuzzy trên nhiều trường
- Lọc theo cột
- Xuất dữ liệu sang CSV, Excel và JSON
- Hỗ trợ biến môi trường để quản lý API key

Phụ thuộc:
- requests: Để giao tiếp API
- pandas: Để thao tác dữ liệu
- customtkinter: Để các thành phần GUI hiện đại
- thefuzz: Để so khớp chuỗi fuzzy
- python-dotenv: Để tải biến môi trường

Tác giả: [Tên của bạn]
Ngày: Tháng 10 năm 2025
"""

import requests
import pandas as pd
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from thefuzz import fuzz
import re
import os
import sys
from dotenv import load_dotenv


class EmployeeApp:
    """
    Lớp ứng dụng chính để Quản lý Nhân viên HRM.

    Lớp này bao gồm tất cả chức năng để lấy dữ liệu nhân viên từ API,
    cung cấp cả giao diện GUI và console để thao tác dữ liệu, và hỗ trợ
    nhiều định dạng xuất khác nhau.

    Thuộc tính:
        df (pd.DataFrame): Dữ liệu nhân viên gốc từ API
        filtered_df (pd.DataFrame): Dữ liệu hiện tại được lọc/hiển thị
        tree (ttk.Treeview): Widget bảng GUI để hiển thị nhân viên
        column_filters (dict): Bộ lọc cột đang hoạt động
        root (ctk.CTk): Cửa sổ GUI chính
        emp_window (ctk.CTkToplevel): Cửa sổ hiển thị nhân viên
    """

    def __init__(self):
        """
        Khởi tạo instance EmployeeApp.

        Thiết lập cấu trúc dữ liệu ban đầu, tải biến môi trường,
        và chuẩn bị thiết lập GUI.
        """
        # Khởi tạo cấu trúc dữ liệu
        self.df = pd.DataFrame()  # Dữ liệu nhân viên gốc
        self.filtered_df = pd.DataFrame()  # Dữ liệu đã lọc để hiển thị
        self.tree = None  # Widget bảng GUI
        self.column_filters = {}  # Từ điển các bộ lọc cột đang hoạt động
        self.is_exporting = False  # Cờ để ngăn xuất đồng thời
        self.export_var = None  # Biến lựa chọn định dạng xuất
        self.filter_pending = None  # Biến debounce cho các thao tác lọc

        # Thiết lập đường dẫn .env thành thuộc tính instance (sửa lỗi thiếu self.env_path)
        self.env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(self.env_path)

        # Thiết lập giao diện người dùng đồ họa
        self.setup_gui()
    
    def setup_gui(self):
        """
        Thiết lập giao diện người dùng đồ họa chính.

        Cấu hình giao diện CustomTkinter, tạo cửa sổ chính,
        và khởi tạo tất cả các thành phần GUI bao gồm nhập API key,
        nút lấy dữ liệu và hiển thị trạng thái.
        """
        # Cấu hình cài đặt giao diện CustomTkinter
        ctk.set_appearance_mode("light")  # Sử dụng chủ đề sáng
        ctk.set_default_color_theme("blue")  # Đặt chủ đề màu xanh

        # Tạo cửa sổ ứng dụng chính
        self.root = ctk.CTk()
        self.root.title("Quản lý nhân viên HRM")  # HRM Employee Manager
        self.root.geometry("500x300")  # Đặt kích thước cửa sổ
        self.root.resizable(False, False)  # Vô hiệu hóa thay đổi kích thước cửa sổ

        # Tạo khung chính để chứa tất cả các thành phần
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Thêm nhãn tiêu đề
        title_label = ctk.CTkLabel(main_frame, text="HRM Employee Manager",
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 30))

        # Tạo phần nhập API key
        api_label = ctk.CTkLabel(main_frame, text="Nhập API Key:",
                               font=ctk.CTkFont(size=14))
        api_label.pack(pady=(0, 10))

        self.api_entry = ctk.CTkEntry(main_frame, placeholder_text="Nhập API key của bạn...",
                                    width=300, show="*")  # Che dữ liệu để bảo mật
        self.api_entry.pack(pady=(0, 20))

        # Tải API key từ môi trường nếu có sẵn
        api_key = os.getenv('API_KEY')
        if api_key:
            self.api_entry.insert(0, api_key)  # Điền sẵn từ biến môi trường

        # Tạo nút lấy dữ liệu
        self.fetch_btn = ctk.CTkButton(main_frame, text="Lấy danh sách nhân viên",
                                     command=self.fetch_employees,  # Gắn với phương thức lấy dữ liệu
                                     width=200, height=40)
        self.fetch_btn.pack(pady=(0, 20))

        # Tạo nhãn trạng thái để phản hồi
        self.status_label = ctk.CTkLabel(main_frame, text="",
                                       font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10))
        
    def save_api_key(self, api_key: str):
        """Tạo hoặc cập nhật .env với API_KEY (chỉ khi thiếu hoặc khác)"""
        try:
            # Đảm bảo đã có self.env_path (phòng khi gọi sớm)
            if not hasattr(self, 'env_path'):
                self.env_path = os.path.join(os.path.dirname(__file__), '.env')
            current = os.getenv('API_KEY')
            if (not os.path.exists(self.env_path)) or (not current) or (current != api_key):
                lines = []
                if os.path.exists(self.env_path):
                    with open(self.env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    # Loại dòng API_KEY cũ
                    lines = [l for l in lines if not l.strip().startswith('API_KEY=')]
                lines.append(f"API_KEY={api_key}\n")
                with open(self.env_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                # Cập nhật ngay biến môi trường trong tiến trình hiện tại
                os.environ['API_KEY'] = api_key
        except Exception as e:
            if hasattr(self, 'root'):
                messagebox.showwarning("Cảnh báo", f"Không thể ghi .env: {e}")
            else:
                print(f"Warning: cannot write .env file: {e}")
    
    def fetch_employees(self):
        """
        Lấy dữ liệu nhân viên từ HRM API.

        Truy xuất danh sách nhân viên bằng API key được cung cấp, xử lý dữ liệu,
        và chuẩn bị để hiển thị. Cập nhật UI với trạng thái và xử lý lỗi.

        Raises:
            Hiển thị messagebox lỗi cho các điều kiện thất bại khác nhau.
        """
        # Lấy và xác thực API key
        api_key = self.api_entry.get().strip()

        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API key!")
            return
        
        # Lưu/ cập nhật .env ngay khi người dùng nhập (lần đầu hoặc đổi)
        self.save_api_key(api_key)
        
        self.status_label.configure(text="Đang lấy dữ liệu...")
        self.fetch_btn.configure(state="disabled")  # Vô hiệu hóa nút trong khi lấy dữ liệu
        self.root.update()  # Buộc cập nhật UI

        try:
            # Xác định điểm cuối API và tham số
            url = "https://hrm.base.vn/extapi/v1/employee/list"
            payload = {
                "access_token": api_key,
                "page": 1,  # Bắt đầu từ trang đầu
                "limit": 50  # Giới hạn kết quả mỗi trang
            }

            # Thực hiện yêu cầu POST tới API
            response = requests.post(url, data=payload)

            if response.status_code == 200:
                # Phân tích cú pháp phản hồi JSON
                data = response.json()

                if data and 'employees' in data:
                    employees = data['employees']
                    if employees:
                        # Xử lý và biến đổi dữ liệu nhân viên
                        self.df = pd.DataFrame(employees)

                        # Trích xuất và định dạng các trường cụ thể
                        self.df['email'] = self.df.apply(lambda x: x.get('email'), axis=1)
                        self.df['phone'] = self.df.apply(lambda x: x.get('phone'), axis=1)
                        self.df['dob'] = self.df.apply(
                            lambda x: f"{x.get('dob_day')}/{x.get('dob_month')}/{x.get('dob_year')}",
                            axis=1
                        )
                        self.df['position'] = self.df.apply(lambda x: x.get('title'), axis=1)
                        self.df['bank_account'] = self.df.apply(
                            lambda x: x.get('bank', {}).get('number'), axis=1
                        )
                        self.df['bank_name'] = self.df.apply(
                            lambda x: x.get('bank', {}).get('name'), axis=1
                        )

                        # Thêm cột số thứ tự (STT - Số thứ tự)
                        self.df.reset_index(drop=True, inplace=True)
                        self.df.insert(0, 'stt', range(1, len(self.df) + 1))

                        # Khởi tạo bản sao dữ liệu đã lọc
                        self.filtered_df = self.df.copy()

                        # Cập nhật trạng thái và hiển thị cửa sổ nhân viên
                        self.status_label.configure(text=f"Lấy thành công {len(self.df)} nhân viên")
                        self.show_employees_window()
                    else:
                        messagebox.showwarning("Cảnh báo", "Danh sách nhân viên trống!")
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu nhân viên!")
            else:
                messagebox.showerror("Lỗi", f"API trả về lỗi: {response.status_code}")

        except requests.exceptions.RequestException as e:
            # Xử lý lỗi liên quan đến mạng
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối đến API: {str(e)}")
        except Exception as e:
            # Xử lý bất kỳ lỗi không mong muốn nào khác
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
        finally:
            # Luôn luôn kích hoạt lại nút lấy dữ liệu
            self.fetch_btn.configure(state="normal")
    
    def show_employees_window(self):
        """
        Hiển thị cửa sổ dữ liệu nhân viên với bảng, tìm kiếm và điều khiển lọc.

        Tạo một cửa sổ modal mới chứa:
        - Bảng dữ liệu nhân viên với sắp xếp và lọc
        - Thanh tìm kiếm với so khớp fuzzy
        - Chức năng xuất dữ liệu
        - Hiển thị thống kê
        """
        # Tạo cửa sổ modal để hiển thị nhân viên
        self.emp_window = ctk.CTkToplevel(self.root)
        self.emp_window.title("Danh sách nhân viên - HRM Manager Pro")
        self.emp_window.geometry("1400x800")
        self.emp_window.grab_set()  # Làm cho cửa sổ modal
        
        # Khung container chính
        main_frame = ctk.CTkFrame(self.emp_window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Phần header với tiêu đề và thông tin
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 15))
        
        # Tiêu đề hiển thị số lượng dữ liệu hiện tại
        self.title_label = ctk.CTkLabel(header_frame, text=f"Danh sách nhân viên ({len(self.filtered_df)} / {len(self.df)} người)", 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=15)
        
        # Phần tìm kiếm và lọc
        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # Ô nhập tìm kiếm fuzzy
        search_label = ctk.CTkLabel(search_frame, text="🔍 Tìm kiếm:", font=ctk.CTkFont(size=14))
        search_label.pack(side="left", padx=(15, 10), pady=15)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Nhập tên, email, số điện thoại... (Fuzzy Search)", 
                                        width=300)
        self.search_entry.pack(side="left", padx=(0, 15), pady=15)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)  # Gắn với trình xử lý tìm kiếm
        
        # Nút xóa tìm kiếm
        clear_btn = ctk.CTkButton(search_frame, text="Xóa", command=self.clear_search, width=60)
        clear_btn.pack(side="left", padx=(0, 15), pady=15)
        
        # Văn bản hướng dẫn để lọc cột
        help_label = ctk.CTkLabel(search_frame, text="💡 Click vào tiêu đề cột để lọc dữ liệu", 
                                font=ctk.CTkFont(size=12))
        help_label.pack(side="right", padx=(15, 15), pady=15)
        
        # Container bảng với panel lọc
        table_container = ctk.CTkFrame(main_frame)
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        # Khung lọc ẩn (hiển thị khi nhấp vào tiêu đề cột)
        self.filter_frame = ctk.CTkFrame(table_container)
        self.filter_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.filter_frame.pack_forget()  # Ban đầu ẩn
        
        # Khung bảng với thanh cuộn
        table_frame = tk.Frame(table_container)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tạo thanh cuộn cho bảng
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Xác định cột để hiển thị (STT + tất cả cột dữ liệu)
        self.show_cols = ['stt'] + list(self.df.columns)

        # Tạo widget Treeview để hiển thị dữ liệu
        self.tree = ttk.Treeview(table_frame, 
                               columns=self.show_cols, 
                               show="headings",  # Ẩn cột đầu mặc định
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)
        
        # Cấu hình thanh cuộn
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Ánh xạ tiêu đề cột
        self.headers = {}
        for col in self.show_cols:
            if col == 'stt':
                self.headers[col] = 'STT'
            elif col == 'id':
                self.headers[col] = 'ID'
            elif col == 'code':
                self.headers[col] = 'Mã NV'
            elif col == 'name':
                self.headers[col] = 'Họ tên'
            elif col == 'email':
                self.headers[col] = 'Email'
            elif col == 'phone':
                self.headers[col] = 'Số điện thoại'
            elif col == 'dob':
                self.headers[col] = 'Ngày sinh'
            elif col == 'position':
                self.headers[col] = 'Chức vụ'
            elif col == 'bank_account':
                self.headers[col] = 'Số TK'
            elif col == 'bank_name':
                self.headers[col] = 'Ngân hàng'
            else:
                # Tiêu đề mặc định cho cột mới
                self.headers[col] = col.replace('_', ' ').title()
        
        # Cấu hình tiêu đề cột với ràng buộc lọc
        for col in self.show_cols:
            self.tree.heading(col, text=f"{self.headers.get(col, col)} ▼", 
                            command=lambda c=col: self.show_column_filter(c))
            # Chiều rộng sẽ được đặt trong refresh_table
        
        # Tải dữ liệu ban đầu vào bảng
        self.refresh_table()
        
        # Ngăn nhấp đúp kích hoạt lọc
        self.tree.bind("<Double-1>", lambda e: None)
        
        # Khung cho các nút điều khiển
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Menu thả xuống xuất dữ liệu
        self.export_var = tk.StringVar(value="Chọn định dạng xuất")
        export_options = ["Chọn định dạng xuất", "CSV", "Excel", "JSON"]
        export_menu = ctk.CTkOptionMenu(btn_frame, 
                                      values=export_options,
                                      variable=self.export_var,
                                      command=self.handle_export,
                                      width=150)
        export_menu.pack(side="left", padx=(15, 10), pady=12)
        
        # Nút làm mới
        refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Làm mới", 
                                  command=self.refresh_all,
                                  width=120)
        refresh_btn.pack(side="left", padx=(0, 10), pady=12)
        
        # Thông tin thống kê
        self.stats_label = ctk.CTkLabel(btn_frame, text=f"Hiển thị: {len(self.filtered_df)} nhân viên", 
                                       font=ctk.CTkFont(size=12))
        self.stats_label.pack(side="left", padx=(20, 0), pady=12)
        
        # Nút đóng
        close_btn = ctk.CTkButton(btn_frame, text="❌ Đóng", 
                                command=self.emp_window.destroy,
                                width=100)
        close_btn.pack(side="right", padx=(10, 15), pady=12)

    def on_search_change(self, event=None):
        """
        Xử lý thay đổi đầu vào tìm kiếm với so khớp fuzzy.

        Cập nhật dữ liệu đã lọc dựa trên văn bản tìm kiếm trên nhiều cột
        bằng cách sử dụng so khớp chuỗi fuzzy với ngưỡng tương đồng 60%.
        """
        search_text = self.search_entry.get().strip()
        if not search_text or self.df.empty:
            self.filtered_df = self.df.copy()
        else:
            # Tìm kiếm fuzzy trên các cột chính
            search_columns = ['name', 'email', 'phone', 'code', 'position']
            mask = pd.Series([False] * len(self.df))

            for i, (idx, row) in enumerate(self.df.iterrows()):
                for col in search_columns:
                    if col in self.df.columns and pd.notna(row[col]):
                        # Sử dụng so khớp fuzzy để tìm kiếm linh hoạt
                        similarity = fuzz.partial_ratio(search_text.lower(), str(row[col]).lower())
                        if similarity >= 60:  # Ngưỡng tương đồng
                            mask.iloc[i] = True
                            break

            self.filtered_df = self.df[mask].copy()

        # Áp dụng lại bộ lọc cột và làm mới hiển thị
        self.apply_column_filters()
        self.refresh_table()
    
    def clear_search(self):
        """Xóa nội dung tìm kiếm"""
        self.search_entry.delete(0, 'end')
        if not self.df.empty:
            self.filtered_df = self.df.copy()
            self.apply_column_filters()
            self.refresh_table()
    
    def show_column_filter(self, column):
        """Hiển thị bộ lọc cho cột được chọn"""
        if self.filter_pending is not None:
            return  # Debounce
        
        self.filter_pending = column
        self.root.after(200, lambda: self.do_show_column_filter(column))
    
    def apply_text_filter(self, column, filter_text):
        """Áp dụng filter dạng text"""
        if not filter_text.strip():
            if column in self.column_filters:
                del self.column_filters[column]
        else:
            self.column_filters[column] = filter_text.strip().lower()
        
        self.apply_column_filters()
        self.refresh_table()
    
    def apply_option_filter(self, column, selected_value):
        """Áp dụng filter dạng option menu"""
        if selected_value == "-- Tất cả --":
            if column in self.column_filters:
                del self.column_filters[column]
        else:
            self.column_filters[column] = selected_value
        
        self.apply_column_filters()
        self.refresh_table()
    
    def apply_column_filters(self):
        """Áp dụng tất cả các filter cột"""
        if self.df.empty:
            self.filtered_df = pd.DataFrame()
            return
            
        temp_df = self.df.copy()
        
        # Áp dụng search filter trước
        search_text = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
        if search_text:
            search_columns = ['name', 'email', 'phone', 'code', 'position']
            mask = pd.Series([False] * len(temp_df))
            
            for i, (_, row) in enumerate(temp_df.iterrows()):
                for col in search_columns:
                    if col in temp_df.columns:
                        val = row[col]
                        if val is not None and not (isinstance(val, float) and pd.isna(val)):
                            similarity = fuzz.partial_ratio(search_text.lower(), str(val).lower())
                            if similarity >= 60:
                                mask.iloc[i] = True
                                break
            
            temp_df = temp_df[mask]
        
        # Áp dụng column filters
        for column, filter_value in self.column_filters.items():
            if isinstance(filter_value, str) and len(filter_value) > 0 and column in temp_df.columns:
                # Bộ lọc văn bản (khớp một phần)
                mask = temp_df[column].astype(str).str.lower().str.contains(filter_value, na=False, regex=False)
                temp_df = temp_df[mask]
        
        self.filtered_df = temp_df
    
    def reset_column_filter(self, column):
        """Reset filter cho một cột"""
        if column in self.column_filters:
            del self.column_filters[column]
        self.apply_column_filters()
        self.refresh_table()
    
    def do_show_column_filter(self, column):
        """Thực hiện hiển thị bộ lọc sau debounce"""
        if self.filter_pending != column:
            return
        self.filter_pending = None
        
        # Chuyển đổi hiển thị khung bộ lọc
        if self.filter_frame.winfo_viewable():
            self.filter_frame.pack_forget()
            return
        
        # Xóa các bộ lọc hiện có trong khung
        for widget in self.filter_frame.winfo_children():
            widget.destroy()
        
        self.filter_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Tạo filter cho cột được chọn
        if column == 'stt':
            return  # Không filter cho cột STT
            
        filter_label = ctk.CTkLabel(self.filter_frame, text=f"Lọc cột '{self.headers[column]}':")
        filter_label.pack(side="left", padx=(15, 10), pady=10)
        
        # Lấy các giá trị unique cho cột
        if self.df.empty or column not in self.df.columns:
            return
        unique_values = self.df[column].dropna().unique()
        unique_values = sorted([str(v) for v in unique_values])
        
        # Combobox cho filter
        if len(unique_values) > 20:
            # Nếu quá nhiều giá trị, dùng Entry box
            filter_entry = ctk.CTkEntry(self.filter_frame, placeholder_text=f"Nhập giá trị {self.headers[column]}...")
            filter_entry.pack(side="left", padx=(0, 10), pady=10)
            filter_entry.bind("<KeyRelease>", lambda e: self.apply_text_filter(column, filter_entry.get()))
        else:
            # Nếu ít giá trị, dùng OptionMenu
            filter_var = tk.StringVar(value="-- Tất cả --")
            filter_values = ["-- Tất cả --"] + unique_values
            
            filter_menu = ctk.CTkOptionMenu(self.filter_frame, 
                                          values=filter_values,
                                          variable=filter_var,
                                          command=lambda val: self.apply_option_filter(column, val))
            filter_menu.pack(side="left", padx=(0, 10), pady=10)
        
        # Nút đóng filter
        close_filter_btn = ctk.CTkButton(self.filter_frame, text="Đóng", 
                                       command=self.close_filter,
                                       width=60)
        close_filter_btn.pack(side="right", padx=(10, 15), pady=10)
        
        # Nút reset filter
        reset_filter_btn = ctk.CTkButton(self.filter_frame, text="Reset", 
                                       command=lambda: self.reset_column_filter(column),
                                       width=60)
        reset_filter_btn.pack(side="right", padx=(0, 10), pady=10)
    
    def close_filter(self):
        """Đóng panel filter"""
        self.filter_frame.pack_forget()
    
    def refresh_table(self):
        """
        Làm mới hiển thị bảng dữ liệu với dữ liệu đã lọc hiện tại.

        Xóa các hàng bảng hiện có và điền lại với dữ liệu đã lọc,
        cập nhật tiêu đề cột và nhãn thống kê.
        """
        if not hasattr(self, 'tree') or self.tree is None or self.filtered_df.empty:
            return

        # Xóa dữ liệu bảng hiện có
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Điền bảng với dữ liệu đã lọc
        for idx, (_, row) in enumerate(self.filtered_df.iterrows(), 1):
            values = [str(idx)]  # Số thứ tự (STT)
            for col in self.show_cols[1:]:  # Bỏ qua cột STT
                if col in self.filtered_df.columns:
                    val = row[col]
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        values.append("")
                    else:
                        values.append(str(val))
                else:
                    values.append("")
            self.tree.insert("", "end", values=values)

        # Cập nhật nhãn hiển thị với số lượng hiện tại
        if hasattr(self, 'title_label'):
            total = len(self.df)
            filtered = len(self.filtered_df)
            self.title_label.configure(text=f"Danh sách nhân viên ({filtered} / {total} người)")

        if hasattr(self, 'stats_label'):
            filtered = len(self.filtered_df)
            self.stats_label.configure(text=f"Hiển thị: {filtered} nhân viên")

        # Tự động điều chỉnh kích thước cột dựa trên nội dung
        self.auto_resize_columns()
    
    def auto_resize_columns(self):
        """Tự động điều chỉnh chiều rộng cột dựa trên nội dung"""
        if not hasattr(self, 'tree') or self.tree is None or self.filtered_df.empty:
            return
        
        # Thuộc tính font để tính chiều rộng (khoảng 8 pixel mỗi ký tự)
        char_width = 8
        min_width = 60
        max_width = 400
        
        for col in self.show_cols:
            if col not in self.filtered_df.columns:
                continue
            
            # Tính max length của header và data
            header_text = self.headers.get(col, col)
            header_len = len(header_text)
            
            # Tính max length trong data (giới hạn 1000 rows để performance)
            sample_data = self.filtered_df[col].head(1000)
            max_data_len = max((len(str(val)) for val in sample_data), default=0)
            
            # Chiều rộng = max(header, data) * char_width + padding
            content_width = max(header_len, max_data_len) * char_width + 20
            
            # Giới hạn min/max
            final_width = max(min_width, min(content_width, max_width))
            
            # Set anchor dựa trên kiểu dữ liệu
            if col == 'stt':
                anchor = "center"
            elif col in ['id', 'code']:
                anchor = "center"
            elif col in ['name', 'email', 'position']:
                anchor = "w"
            else:
                anchor = "center"
            
            self.tree.column(col, width=final_width, anchor=anchor)
    
    def refresh_all(self):
        """Làm mới toàn bộ dữ liệu"""
        # Đặt lại bộ lọc
        self.column_filters = {}
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, 'end')
        
        # Tải lại dữ liệu
        self.filtered_df = self.df.copy()
        self.refresh_table()
        
        # Ẩn filter panel
        if hasattr(self, 'filter_frame'):
            self.filter_frame.pack_forget()
    
    def export_csv(self):
        if self.filtered_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Lưu file CSV"
        )
        
        if filename:
            try:
                self.filtered_df.to_csv(filename, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Thành công", f"Đã xuất {len(self.filtered_df)} nhân viên ra file CSV: {filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file CSV: {str(e)}")
    
    def export_excel(self):
        if self.filtered_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Lưu file Excel"
        )
        
        if filename:
            try:
                self.filtered_df.to_excel(filename, index=False)
                messagebox.showinfo("Thành công", f"Đã xuất {len(self.filtered_df)} nhân viên ra file Excel: {filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file Excel: {str(e)}")
    
    def export_json(self):
        if self.filtered_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Lưu file JSON"
        )
        
        if filename:
            try:
                self.filtered_df.to_json(filename, orient='records', indent=4, force_ascii=False)
                messagebox.showinfo("Thành công", f"Đã xuất {len(self.filtered_df)} nhân viên ra file JSON: {filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file JSON: {str(e)}")
    
    def handle_export(self, selected_format):
        """
        Xử lý lựa chọn định dạng xuất từ menu thả xuống.

        Ngăn xuất đồng thời và ủy quyền cho phương thức xuất thích hợp
        dựa trên định dạng đã chọn (CSV, Excel, JSON).
        """
        if self.is_exporting or selected_format == "Chọn định dạng xuất":
            return

        self.is_exporting = True
        try:
            if selected_format == "CSV":
                self.export_csv()
            elif selected_format == "Excel":
                self.export_excel()
            elif selected_format == "JSON":
                self.export_json()
        finally:
            self.is_exporting = False
            if self.export_var:
                self.export_var.set("Chọn định dạng xuất")
    
    def run(self):
        """Khởi động vòng lặp chính của ứng dụng GUI."""
        self.root.mainloop()
    
    def console_run(self):
        print("HRM Employee Manager - Console Mode")
        print("=" * 50)
        if not hasattr(self, 'env_path'):
            self.env_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(self.env_path)
        api_key_input = input("Enter your API key (press Enter to use from .env): ").strip()
        if api_key_input:
            # Người dùng cung cấp key mới
            self.save_api_key(api_key_input)
            print("Saved API key to .env for future runs.")
            api_key = api_key_input
        else:
            api_key = os.getenv('API_KEY')
            if api_key:
                print("Using API key from .env file")
            else:
                print("Error: API key is required!")
                sys.exit(1)
        print("Fetching employee data...")
        try:
            # URL API
            url = "https://hrm.base.vn/extapi/v1/employee/list"
            
            # Payload
            payload = {
                "access_token": api_key,
                "page": 1,
                "limit": 50
            }
            
            # Gửi yêu cầu POST
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'employees' in data:
                    employees = data['employees']
                    if employees:
                        # Xử lý dữ liệu
                        self.df = pd.DataFrame(employees)
                        self.df['email'] = self.df.apply(lambda x: x.get('email'), axis=1)
                        self.df['phone'] = self.df.apply(lambda x: x.get('phone'), axis=1)
                        self.df['dob'] = self.df.apply(lambda x: f"{x.get('dob_day')}/{x.get('dob_month')}/{x.get('dob_year')}", axis=1)
                        self.df['position'] = self.df.apply(lambda x: x.get('title'), axis=1)
                        self.df['bank_account'] = self.df.apply(lambda x: x.get('bank', {}).get('number'), axis=1)
                        self.df['bank_name'] = self.df.apply(lambda x: x.get('bank', {}).get('name'), axis=1)
                        
                        # Thêm cột STT
                        self.df.reset_index(drop=True, inplace=True)
                        self.df.insert(0, 'stt', range(1, len(self.df) + 1))
                        
                        # Khởi tạo dữ liệu đã lọc
                        self.filtered_df = self.df.copy()
                        self.column_filters = {}
                        self.search_text = ""
                        
                        print(f"Successfully fetched {len(self.df)} employees.")
                        
                        # Vòng lặp menu chính
                        self.console_main_menu()
                    else:
                        print("Warning: Employee list is empty!")
                else:
                    print("Error: No employee data found!")
            else:
                print(f"Error: API returned error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
        except Exception as e:
            print(f"Đã xảy ra lỗi: {str(e)}")
    
    def console_main_menu(self):
        """Menu chính cho giao diện console"""
        while True:
            print("\n" + "=" * 50)
            print("HRM EMPLOYEE MANAGER - CONSOLE MENU")
            print("=" * 50)
            print(f"Total employees: {len(self.df)} | Filtered: {len(self.filtered_df)}")
            print("=" * 50)
            print("1. 🔍 Search employees (Fuzzy search)")
            print("2. 🔽 Filter by column")
            print("3. 📊 Sort by column")
            print("4. 📋 Display employees")
            print("5. 📈 Statistics")
            print("6. 📄 Export data")
            print("7. 🔄 Reset filters")
            print("8. ❌ Exit")
            print("=" * 50)
            
            choice = input("Choose an option (1-8): ").strip()
            
            if choice == '1':
                self.console_search()
            elif choice == '2':
                self.console_filter()
            elif choice == '3':
                self.console_sort()
            elif choice == '4':
                self.console_display()
            elif choice == '5':
                self.console_statistics()
            elif choice == '6':
                self.console_export()
            elif choice == '7':
                self.console_reset()
            elif choice == '8':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def console_search(self):
        """Chức năng tìm kiếm console"""
        print("\n🔍 FUZZY SEARCH")
        print("-" * 30)
        current_search = self.search_text if hasattr(self, 'search_text') and self.search_text else ""
        print(f"Current search: '{current_search}'")
        
        search_text = input("Enter search text (name, email, phone, code, position): ").strip()
        
        if search_text:
            self.search_text = search_text
            self.apply_console_filters()
            print(f"✅ Found {len(self.filtered_df)} matching employees")
        else:
            self.search_text = ""
            self.apply_console_filters()
            print("✅ Search cleared")
    
    def console_filter(self):
        """Chức năng lọc console"""
        print("\n🔽 COLUMN FILTER")
        print("-" * 30)
        
        # Hiển thị bộ lọc hiện tại
        if self.column_filters:
            print("Current filters:")
            for col, val in self.column_filters.items():
                print(f"  {col}: {val}")
        else:
            print("No active filters")
        
        print("\nAvailable columns:")
        columns = {
            '1': ('name', 'Họ tên'),
            '2': ('email', 'Email'),
            '3': ('phone', 'Số điện thoại'),
            '4': ('code', 'Mã NV'),
            '5': ('position', 'Chức vụ'),
            '6': ('bank_name', 'Ngân hàng')
        }
        
        for key, (col, name) in columns.items():
            print(f"{key}. {name}")
        print("7. Clear all filters")
        print("8. Back to main menu")
        
        choice = input("Choose column to filter (1-8): ").strip()
        
        if choice == '8':
            return
        elif choice == '7':
            self.column_filters = {}
            self.apply_console_filters()
            print("✅ All filters cleared")
            return
        
        if choice in columns:
            col, name = columns[choice]
            print(f"\nFiltering by: {name}")
            
            # Lấy các giá trị duy nhất cho cột này
            if col in self.df.columns:
                unique_values = self.df[col].dropna().unique()
                unique_values = sorted([str(v) for v in unique_values if v])
                
                if len(unique_values) <= 10:
                    print("Available values:")
                    for i, val in enumerate(unique_values[:10], 1):
                        print(f"{i}. {val}")
                    print("11. Enter custom value")
                    
                    val_choice = input("Choose value or enter 11 for custom: ").strip()
                    
                    if val_choice == '11':
                        filter_val = input("Enter filter value: ").strip()
                    elif val_choice.isdigit() and 1 <= int(val_choice) <= len(unique_values):
                        filter_val = unique_values[int(val_choice) - 1]
                    else:
                        print("Invalid choice")
                        return
                else:
                    filter_val = input("Enter filter value (partial match): ").strip()
                
                if filter_val:
                    self.column_filters[col] = filter_val.lower()
                    self.apply_console_filters()
                    print(f"✅ Filter applied: {name} contains '{filter_val}'")
                else:
                    if col in self.column_filters:
                        del self.column_filters[col]
                    self.apply_console_filters()
                    print(f"✅ Filter for {name} cleared")
    
    def console_sort(self):
        """Chức năng sắp xếp console"""
        print("\n📊 SORT BY COLUMN")
        print("-" * 30)
        
        columns = {
            '1': ('name', 'Họ tên'),
            '2': ('email', 'Email'),
            '3': ('code', 'Mã NV'),
            '4': ('position', 'Chức vụ'),
            '5': ('stt', 'STT')
        }
        
        for key, (col, name) in columns.items():
            print(f"{key}. {name}")
        print("6. Back to main menu")
        
        choice = input("Choose column to sort by (1-6): ").strip()
        
        if choice == '6':
            return
        
        if choice in columns:
            col, name = columns[choice]
            
            print("Sort order:")
            print("1. Ascending (A-Z, 1-9)")
            print("2. Descending (Z-A, 9-1)")
            
            order_choice = input("Choose order (1-2): ").strip()
            
            if order_choice in ['1', '2']:
                ascending = order_choice == '1'
                
                try:
                    self.filtered_df = self.filtered_df.sort_values(by=col, ascending=ascending)
                    print(f"✅ Sorted by {name} ({'ascending' if ascending else 'descending'})")
                except Exception as e:
                    print(f"❌ Error sorting: {str(e)}")
            else:
                print("Invalid choice")
    
    def console_display(self):
        """Chức năng hiển thị console với phân trang"""
        print("\n📋 DISPLAY EMPLOYEES")
        print("-" * 30)
        
        if self.filtered_df.empty:
            print("No employees to display")
            return
        
        # Tùy chọn hiển thị
        print("Display options:")
        print("1. Show all employees")
        print("2. Show with pagination (10 per page)")
        print("3. Show specific columns")
        print("4. Back to main menu")
        
        choice = input("Choose display option (1-4): ").strip()
        
        if choice == '4':
            return
        
        # Column selection - tạo động từ data
        all_cols = {}
        for i, col in enumerate(['stt'] + list(self.df.columns), 1):
            all_cols[str(i)] = col
        
        display_cols = ['stt'] + list(self.df.columns)[:5]  # Mặc định hiển thị STT + 5 cột đầu
        
        if choice == '3':
            print("\nAvailable columns:")
            for key, col in all_cols.items():
                print(f"{key}. {col}")
            
            col_choice = input("Enter column numbers (comma-separated, e.g., 1,2,3): ").strip()
            
            try:
                selected_indices = [int(x.strip()) for x in col_choice.split(',')]
                display_cols = [all_cols[str(i)] for i in selected_indices if str(i) in all_cols]
                if not display_cols:
                    display_cols = ['stt'] + list(self.df.columns)[:5]
            except:
                print("Invalid selection, using default columns")
        
        # Hiển thị dữ liệu
        if choice == '1':
            # Hiển thị tất cả với định dạng tốt hơn
            print(f"\nShowing all {len(self.filtered_df)} employees:")
            # Giới hạn chiều rộng cột để hiển thị tốt hơn
            display_df = self.filtered_df[display_cols].copy()
            
            # Cắt ngắn các cột dài
            for col in display_cols:
                if col in ['name', 'email', 'position']:
                    display_df[col] = display_df[col].astype(str).str.slice(0, 30)
            
            print(display_df.to_string(index=False, max_colwidth=30))
            
        elif choice == '2':
            # Phân trang với định dạng tốt hơn
            page_size = 10
            total_pages = (len(self.filtered_df) + page_size - 1) // page_size
            
            current_page = 1
            
            while True:
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(self.filtered_df))
                
                print(f"\nPage {current_page}/{total_pages} (showing {start_idx+1}-{end_idx} of {len(self.filtered_df)})")
                
                # Định dạng hiển thị
                page_df = self.filtered_df[display_cols].iloc[start_idx:end_idx].copy()
                for col in display_cols:
                    if col in ['name', 'email', 'position']:
                        page_df[col] = page_df[col].astype(str).str.slice(0, 30)
                
                print(page_df.to_string(index=False, max_colwidth=30))
                
                if total_pages == 1:
                    break
                
                print("\nNavigation:")
                print("n. Next page")
                print("p. Previous page")
                print("g. Go to page")
                print("q. Quit display")
                
                nav_choice = input("Choose (n/p/g/q): ")

                if nav_choice == 'q':
                    break
                elif nav_choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif nav_choice == 'p' and current_page > 1:
                    current_page -= 1
                elif nav_choice == 'g':
                    try:
                        page_num = int(input("Enter page number: ").strip())
                        if 1 <= page_num <= total_pages:
                            current_page = page_num
                        else:
                            print("Invalid page number")
                    except:
                        print("Invalid input")
                
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(self.filtered_df))
                print(f"\nPage {current_page}/{total_pages} (showing {start_idx+1}-{end_idx} of {len(self.filtered_df)})")
                page_df = self.filtered_df[display_cols].iloc[start_idx:end_idx].copy()
                for col in display_cols:
                    if col in ['name', 'email', 'position']:
                        page_df[col] = page_df[col].astype(str).str.slice(0, 30)
                print(page_df.to_string(index=False, max_colwidth=30))
                if total_pages == 1:
                    break
                print("\nNavigation:")
                print("n. Next page")
                print("p. Previous page")
                print("g. Go to page")
                print("q. Quit display")
                nav_choice = input("Choose (n/p/g/q): ").strip().lower()
    
    def console_statistics(self):
        """Chức năng thống kê console"""
        print("\n📈 STATISTICS")
        print("-" * 30)
        if self.filtered_df.empty:
            print("No data to analyze")
            return
        print(f"Total employees: {len(self.filtered_df)}")
        print(f"Original dataset: {len(self.df)}")
        
        # Phân bố giới tính (giả định có thể suy ra từ tên hoặc các trường khác)
        # Vì chúng ta không có trường giới tính rõ ràng, hãy đếm theo vị trí
        if 'position' in self.filtered_df.columns:
            position_counts = self.filtered_df['position'].value_counts()
            print(f"\n📊 Employees by position:")
            for pos, count in position_counts.head(10).items():
                print(f"  {pos}: {count}")
        
        # Tên miền email
        if 'email' in self.filtered_df.columns:
            email_domains = self.filtered_df['email'].dropna().apply(
                lambda x: str(x).split('@')[-1] if '@' in str(x) else 'unknown'
            )
            domain_counts = email_domains.value_counts()
            print(f"\n📧 Email domains:")
            for domain, count in domain_counts.head(5).items():
                print(f"  {domain}: {count}")
        
        # Phân bố ngân hàng
        if 'bank_name' in self.filtered_df.columns:
            bank_counts = self.filtered_df['bank_name'].value_counts()
            print(f"\n🏦 Bank distribution:")
            for bank, count in bank_counts.head(5).items():
                if bank and bank != 'nan':
                    print(f"  {bank}: {count}")

    def console_export(self):
        """Chức năng xuất console"""
        print("\n📄 EXPORT DATA")
        print("-" * 30)
        if self.filtered_df.empty:
            print("No data to export")
            return
        print("Export options:")
        print("1. Export to CSV")
        print("2. Export to Excel")
        print("3. Export to JSON")
        print("4. Export with custom filename")
        print("5. Back to main menu")
        choice = input("Choose export option (1-5): ").strip()
        if choice == '5':
            return
        base_name = "employees"
        if choice == '4':
            base_name = input("Enter base filename (without extension): ").strip() or "employees"
        if choice in ['1', '4']:
            filename = f"{base_name}.csv"
            try:
                self.filtered_df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ Exported {len(self.filtered_df)} employees to {filename}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
        elif choice == '2':
            filename = f"{base_name}.xlsx"
            try:
                self.filtered_df.to_excel(filename, index=False)
                print(f"✅ Exported {len(self.filtered_df)} employees to {filename}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
        elif choice == '3':
            filename = f"{base_name}.json"
            try:
                self.filtered_df.to_json(filename, orient='records', indent=4, force_ascii=False)
                print(f"✅ Exported {len(self.filtered_df)} employees to {filename}")
            except Exception as e:
                print(f"❌ Export failed: {e}")

    def console_reset(self):
        """Đặt lại tất cả bộ lọc và tìm kiếm"""
        self.search_text = ""
        self.column_filters = {}
        self.filtered_df = self.df.copy()
        print("✅ All filters and search cleared")

    def apply_console_filters(self):
        """Áp dụng bộ lọc tìm kiếm và cột cho filtered_df"""
        if self.df.empty:
            self.filtered_df = pd.DataFrame()
            return
        temp_df = self.df.copy()
        
        # Áp dụng bộ lọc tìm kiếm
        search_text = getattr(self, 'search_text', '')
        if search_text:
            search_columns = ['name', 'email', 'phone', 'code', 'position']
            mask = pd.Series([False] * len(temp_df))
            for i, (_, row) in enumerate(temp_df.iterrows()):
                for col in search_columns:
                    if col in temp_df.columns:
                        val = row[col]
                        if val is not None and not (isinstance(val, float) and pd.isna(val)):
                            similarity = fuzz.partial_ratio(search_text.lower(), str(val).lower())
                            if similarity >= 60:
                                mask.iloc[i] = True
                                break
            temp_df = temp_df[mask]
        
        # Áp dụng bộ lọc cột
        for column, filter_value in self.column_filters.items():
            if filter_value and column in temp_df.columns:
                mask = temp_df[column].astype(str).str.lower().str.contains(filter_value, na=False, regex=False)
                temp_df = temp_df[mask]
        self.filtered_df = temp_df

# Điểm nhập chính của ứng dụng
if __name__ == "__main__":
    # Tạo và chạy ứng dụng quản lý nhân viên
    app = EmployeeApp()
    # Kiểm tra xem GUI có khả dụng không (có cửa sổ root)
    if hasattr(app, 'root'):
        app.run()  # Khởi động chế độ GUI
    # Nếu không có GUI, phương thức console_run sẽ được gọi riêng biệt