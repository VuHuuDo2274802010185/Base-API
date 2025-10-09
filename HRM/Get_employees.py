import requests
import pandas as pd
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from thefuzz import fuzz
import re

class EmployeeApp:
    def __init__(self):
        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()
        self.tree = None
        self.column_filters = {}
        self.setup_gui()
    
    def setup_gui(self):
        # Cấu hình CustomTkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Tạo cửa sổ chính
        self.root = ctk.CTk()
        self.root.title("Quản lý nhân viên HRM")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # Tạo frame chính
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tiêu đề
        title_label = ctk.CTkLabel(main_frame, text="HRM Employee Manager", 
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        # Label và Entry cho API key
        api_label = ctk.CTkLabel(main_frame, text="Nhập API Key:", 
                               font=ctk.CTkFont(size=14))
        api_label.pack(pady=(0, 10))
        
        self.api_entry = ctk.CTkEntry(main_frame, placeholder_text="Nhập API key của bạn...", 
                                    width=300, show="*")
        self.api_entry.pack(pady=(0, 20))
        
        # Nút lấy dữ liệu
        self.fetch_btn = ctk.CTkButton(main_frame, text="Lấy danh sách nhân viên", 
                                     command=self.fetch_employees,
                                     width=200, height=40)
        self.fetch_btn.pack(pady=(0, 20))
        
        # Label trạng thái
        self.status_label = ctk.CTkLabel(main_frame, text="", 
                                       font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10))
        
    def fetch_employees(self):
        api_key = self.api_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API key!")
            return
        
        self.status_label.configure(text="Đang lấy dữ liệu...")
        self.fetch_btn.configure(state="disabled")
        self.root.update()
        
        try:
            # URL API
            url = "https://hrm.base.vn/extapi/v1/employee/list"
            
            # Payload
            payload = {
                "access_token": api_key,
                "page": 1,
                "limit": 50
            }
            
            # Gửi POST request
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
                        
                        # Khởi tạo filtered_df
                        self.filtered_df = self.df.copy()
                        
                        self.status_label.configure(text=f"Lấy thành công {len(self.df)} nhân viên")
                        self.show_employees_window()
                    else:
                        messagebox.showwarning("Cảnh báo", "Danh sách nhân viên trống!")
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu nhân viên!")
            else:
                messagebox.showerror("Lỗi", f"API trả về lỗi: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối đến API: {str(e)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
        finally:
            self.fetch_btn.configure(state="normal")
    
    def show_employees_window(self):
        # Tạo cửa sổ hiển thị danh sách nhân viên
        self.emp_window = ctk.CTkToplevel(self.root)
        self.emp_window.title("Danh sách nhân viên - HRM Manager Pro")
        self.emp_window.geometry("1400x800")
        self.emp_window.grab_set()  # Modal window
        
        # Frame chính
        main_frame = ctk.CTkFrame(self.emp_window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Frame header với tiêu đề và thông tin
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 15))
        
        # Tiêu đề
        self.title_label = ctk.CTkLabel(header_frame, text=f"Danh sách nhân viên ({len(self.filtered_df)} / {len(self.df)} người)", 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=15)
        
        # Frame tìm kiếm và lọc
        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # Thanh tìm kiếm fuzzy
        search_label = ctk.CTkLabel(search_frame, text="🔍 Tìm kiếm:", font=ctk.CTkFont(size=14))
        search_label.pack(side="left", padx=(15, 10), pady=15)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Nhập tên, email, số điện thoại... (Fuzzy Search)", 
                                        width=300)
        self.search_entry.pack(side="left", padx=(0, 15), pady=15)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Nút clear search
        clear_btn = ctk.CTkButton(search_frame, text="Xóa", command=self.clear_search, width=60)
        clear_btn.pack(side="left", padx=(0, 15), pady=15)
        
        # Label hướng dẫn
        help_label = ctk.CTkLabel(search_frame, text="💡 Click vào tiêu đề cột để lọc dữ liệu", 
                                font=ctk.CTkFont(size=12))
        help_label.pack(side="right", padx=(15, 15), pady=15)
        
        # Frame cho bảng với filter
        table_container = ctk.CTkFrame(main_frame)
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        # Frame cho filter (ẩn/hiện)
        self.filter_frame = ctk.CTkFrame(table_container)
        self.filter_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.filter_frame.pack_forget()  # Ẩn ban đầu
        
        # Frame cho bảng
        table_frame = tk.Frame(table_container)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview với cột STT đầu tiên
        self.show_cols = ['stt', 'id','code','name','email','phone','dob','position','bank_account','bank_name']
        self.tree = ttk.Treeview(table_frame, 
                               columns=self.show_cols, 
                               show="headings",
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)
        
        # Cấu hình scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Headers với khả năng lọc
        self.headers = {
            'stt': 'STT',
            'id': 'ID',
            'code': 'Mã NV',
            'name': 'Họ tên',
            'email': 'Email', 
            'phone': 'Số điện thoại',
            'dob': 'Ngày sinh',
            'position': 'Chức vụ',
            'bank_account': 'Số TK',
            'bank_name': 'Ngân hàng'
        }
        
        # Cấu hình cột và bind event cho filter
        for col in self.show_cols:
            self.tree.heading(col, text=f"{self.headers.get(col, col)} ▼", 
                            command=lambda c=col: self.show_column_filter(c))
            if col == 'stt':
                self.tree.column(col, width=60, anchor="center")
            elif col in ['id', 'code']:
                self.tree.column(col, width=80, anchor="center")
            elif col in ['name', 'email']:
                self.tree.column(col, width=150, anchor="w")
            else:
                self.tree.column(col, width=120, anchor="center")
        
        # Tải dữ liệu ban đầu
        self.refresh_table()
        
        # Frame cho các nút điều khiển
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Nút xuất CSV
        csv_btn = ctk.CTkButton(btn_frame, text="📄 Xuất CSV", 
                              command=self.export_csv,
                              width=120)
        csv_btn.pack(side="left", padx=(15, 10), pady=12)
        
        # Nút xuất Excel
        excel_btn = ctk.CTkButton(btn_frame, text="📊 Xuất Excel", 
                                command=self.export_excel,
                                width=120)
        excel_btn.pack(side="left", padx=(0, 10), pady=12)
        
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
        """Xử lý sự kiện thay đổi trong ô tìm kiếm"""
        search_text = self.search_entry.get().strip()
        if not search_text or self.df.empty:
            self.filtered_df = self.df.copy()
        else:
            # Fuzzy search trong các cột quan trọng
            search_columns = ['name', 'email', 'phone', 'code', 'position']
            mask = pd.Series([False] * len(self.df))
            
            for i, (idx, row) in enumerate(self.df.iterrows()):
                for col in search_columns:
                    if col in self.df.columns and pd.notna(row[col]):
                        # Sử dụng thefuzz để tìm kiếm fuzzy
                        from thefuzz import fuzz
                        similarity = fuzz.partial_ratio(search_text.lower(), str(row[col]).lower())
                        if similarity >= 60:  # Ngưỡng tương đồng 60%
                            mask.iloc[i] = True
                            break
            
            self.filtered_df = self.df[mask].copy()
        
        # Áp dụng lại các filter cột nếu có
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
        # Toggle filter frame visibility
        if self.filter_frame.winfo_viewable():
            self.filter_frame.pack_forget()
            return
        
        # Clear existing filters in frame
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
                    if col in temp_df.columns and pd.notna(row[col]):
                        from thefuzz import fuzz
                        similarity = fuzz.partial_ratio(search_text.lower(), str(row[col]).lower())
                        if similarity >= 60:
                            mask.iloc[i] = True
                            break
            
            temp_df = temp_df[mask]
        
        # Áp dụng column filters
        for column, filter_value in self.column_filters.items():
            if isinstance(filter_value, str) and len(filter_value) > 0 and column in temp_df.columns:
                # Text filter (partial match)
                mask = temp_df[column].astype(str).str.lower().str.contains(filter_value, na=False, regex=False)
                temp_df = temp_df[mask]
        
        self.filtered_df = temp_df
    
    def reset_column_filter(self, column):
        """Reset filter cho một cột"""
        if column in self.column_filters:
            del self.column_filters[column]
        self.apply_column_filters()
        self.refresh_table()
    
    def close_filter(self):
        """Đóng panel filter"""
        self.filter_frame.pack_forget()
    
    def refresh_table(self):
        """Làm mới bảng hiển thị với dữ liệu đã lọc"""
        if not hasattr(self, 'tree') or self.tree is None or self.filtered_df.empty:
            return
            
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Thêm dữ liệu mới với STT
        for idx, (_, row) in enumerate(self.filtered_df.iterrows(), 1):
            values = [str(idx)]  # STT
            for col in self.show_cols[1:]:  # Bỏ qua cột STT
                if col in self.filtered_df.columns:
                    values.append(str(row[col]) if pd.notna(row[col]) else "")
                else:
                    values.append("")
            self.tree.insert("", "end", values=values)
        
        # Cập nhật labels
        if hasattr(self, 'title_label'):
            total = len(self.df)
            filtered = len(self.filtered_df)
            self.title_label.configure(text=f"Danh sách nhân viên ({filtered} / {total} người)")
        
        if hasattr(self, 'stats_label'):
            filtered = len(self.filtered_df)
            self.stats_label.configure(text=f"Hiển thị: {filtered} nhân viên")
    
    def refresh_all(self):
        """Làm mới toàn bộ dữ liệu"""
        # Reset filters
        self.column_filters = {}
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, 'end')
        
        # Reload data
        self.filtered_df = self.df.copy()
        self.refresh_table()
        
        # Ẩn filter panel
        if hasattr(self, 'filter_frame'):
            self.filter_frame.pack_forget()
    
    def export_csv(self):
        if self.df is None:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Lưu file CSV"
        )
        
        if filename:
            try:
                self.df.to_csv(filename, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Thành công", f"Đã xuất file CSV: {filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file CSV: {str(e)}")
    
    def export_excel(self):
        if self.df is None:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Lưu file Excel"
        )
        
        if filename:
            try:
                self.df.to_excel(filename, index=False)
                messagebox.showinfo("Thành công", f"Đã xuất file Excel: {filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file Excel: {str(e)}")
    
    def run(self):
        self.root.mainloop()

# Chạy ứng dụng
if __name__ == "__main__":
    app = EmployeeApp()
    app.run()