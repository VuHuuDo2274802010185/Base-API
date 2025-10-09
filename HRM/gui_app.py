"""
Ứng dụng GUI cho HRM Employee Manager

Chứa giao diện người dùng đồ họa và các chức năng liên quan.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import os
from .config import GUI_TITLE, GUI_GEOMETRY, GUI_APPEARANCE, GUI_THEME, HEADERS, TABLE_WIDTH, TABLE_HEIGHT
from .data_manager import DataManager
from .utils import format_display_value, get_unique_values


class GUIApp:
    """Ứng dụng GUI chính"""

    def __init__(self):
        # Khởi tạo cấu trúc dữ liệu
        self.data_manager = DataManager()
        self.tree = None
        self.is_exporting = False
        self.export_var = None
        self.filter_pending = None

        # Thiết lập giao diện
        self.setup_gui()

    def setup_gui(self):
        """Thiết lập giao diện người dùng đồ họa chính"""
        ctk.set_appearance_mode(GUI_APPEARANCE)
        ctk.set_default_color_theme(GUI_THEME)

        self.root = ctk.CTk()
        self.root.title(GUI_TITLE)
        self.root.geometry(GUI_GEOMETRY)
        self.root.resizable(False, False)

        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(main_frame, text=GUI_TITLE,
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 30))

        api_label = ctk.CTkLabel(main_frame, text="Nhập API Key:",
                               font=ctk.CTkFont(size=14))
        api_label.pack(pady=(0, 10))

        self.api_entry = ctk.CTkEntry(main_frame, placeholder_text="Nhập API key của bạn...",
                                    width=300, show="*")
        self.api_entry.pack(pady=(0, 20))

        api_key = os.getenv('API_KEY')
        if api_key:
            self.api_entry.insert(0, api_key)

        self.fetch_btn = ctk.CTkButton(main_frame, text="Lấy danh sách nhân viên",
                                     command=self.fetch_employees, width=200, height=40)
        self.fetch_btn.pack(pady=(0, 20))

        self.status_label = ctk.CTkLabel(main_frame, text="",
                                       font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10))

    def fetch_employees(self):
        """Lấy dữ liệu nhân viên"""
        api_key = self.api_entry.get().strip()

        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API key!")
            return

        self.status_label.configure(text="Đang lấy dữ liệu...")
        self.fetch_btn.configure(state="disabled")
        self.root.update()

        count, error = self.data_manager.fetch_employees(api_key)

        self.fetch_btn.configure(state="normal")

        if error:
            messagebox.showerror("Lỗi", error)
            self.status_label.configure(text="")
        else:
            self.status_label.configure(text=f"Lấy thành công {count} nhân viên")
            self.show_employees_window()

    def show_employees_window(self):
        """Hiển thị cửa sổ dữ liệu nhân viên"""
        self.emp_window = ctk.CTkToplevel(self.root)
        self.emp_window.title("Danh sách nhân viên - HRM Manager Pro")
        self.emp_window.geometry(f"{TABLE_WIDTH}x{TABLE_HEIGHT}")
        self.emp_window.grab_set()

        main_frame = ctk.CTkFrame(self.emp_window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 15))

        self.title_label = ctk.CTkLabel(header_frame,
                                       text=f"Danh sách nhân viên ({len(self.data_manager.filtered_df)} / {len(self.data_manager.df)} người)",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=15)

        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", padx=10, pady=(0, 15))

        search_label = ctk.CTkLabel(search_frame, text="🔍 Tìm kiếm:", font=ctk.CTkFont(size=14))
        search_label.pack(side="left", padx=(15, 10), pady=15)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Nhập tên, email, số điện thoại...",
                                        width=300)
        self.search_entry.pack(side="left", padx=(0, 15), pady=15)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

        clear_btn = ctk.CTkButton(search_frame, text="Xóa", command=self.clear_search, width=60)
        clear_btn.pack(side="left", padx=(0, 15), pady=15)

        help_label = ctk.CTkLabel(search_frame, text="💡 Click vào tiêu đề cột để lọc dữ liệu",
                                font=ctk.CTkFont(size=12))
        help_label.pack(side="right", padx=(15, 15), pady=15)

        table_container = ctk.CTkFrame(main_frame)
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.filter_frame = ctk.CTkFrame(table_container)
        self.filter_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.filter_frame.pack_forget()

        table_frame = tk.Frame(table_container)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")

        self.show_cols = ['stt'] + list(self.data_manager.df.columns)

        self.tree = ttk.Treeview(table_frame,
                               columns=self.show_cols,
                               show="headings",
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)

        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.headers = {}
        for col in self.show_cols:
            if col in HEADERS:
                self.headers[col] = HEADERS[col]
            else:
                self.headers[col] = col.replace('_', ' ').title()

        for col in self.show_cols:
            self.tree.heading(col, text=f"{self.headers.get(col, col)} ▼",
                            command=lambda c=col: self.show_column_filter(c))

        # Đặt chiều rộng cố định cho các cột
        for col in self.show_cols:
            if col == 'stt':
                self.tree.column(col, width=60, minwidth=50, anchor="center")
            elif col in ['id', 'code']:
                self.tree.column(col, width=80, minwidth=60, anchor="center")
            elif col in ['name', 'email', 'position']:
                self.tree.column(col, width=150, minwidth=100, anchor="w")
            elif col in ['profile', 'bank', 'form']:
                self.tree.column(col, width=200, minwidth=150, anchor="w")
            else:
                self.tree.column(col, width=100, minwidth=80, anchor="center")

        self.refresh_table()

        self.tree.bind("<Double-1>", lambda e: None)

        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.export_var = tk.StringVar(value="Chọn định dạng xuất")
        export_options = ["Chọn định dạng xuất"] + ["CSV", "Excel", "JSON"]
        export_menu = ctk.CTkOptionMenu(btn_frame, values=export_options,
                                      variable=self.export_var,
                                      command=self.handle_export,
                                      width=150)
        export_menu.pack(side="left", padx=(15, 10), pady=12)

        refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Làm mới",
                                  command=self.refresh_all,
                                  width=120)
        refresh_btn.pack(side="left", padx=(0, 10), pady=12)

        self.stats_label = ctk.CTkLabel(btn_frame, text=f"Hiển thị: {len(self.data_manager.filtered_df)} nhân viên",
                                       font=ctk.CTkFont(size=12))
        self.stats_label.pack(side="left", padx=(20, 0), pady=12)

        close_btn = ctk.CTkButton(btn_frame, text="❌ Đóng",
                                command=self.emp_window.destroy,
                                width=100)
        close_btn.pack(side="right", padx=(10, 15), pady=12)

    def on_search_change(self, event=None):
        """Xử lý thay đổi đầu vào tìm kiếm"""
        start_time = time.time()
        search_text = self.search_entry.get().strip()
        self.data_manager.search_text = search_text
        self.data_manager.apply_filters()
        self.refresh_table()
        total_time = time.time() - start_time
        print(f"Search change time: {total_time:.4f}s")

    def clear_search(self):
        """Xóa nội dung tìm kiếm"""
        self.search_entry.delete(0, 'end')
        self.data_manager.search_text = ""
        self.data_manager.apply_filters()
        self.refresh_table()

    def show_column_filter(self, column):
        """Hiển thị bộ lọc cho cột được chọn"""
        if self.filter_pending is not None:
            return
        self.filter_pending = column
        self.root.after(200, lambda: self.do_show_column_filter(column))

    def do_show_column_filter(self, column):
        """Thực hiện hiển thị bộ lọc sau debounce"""
        if self.filter_pending != column:
            return
        self.filter_pending = None

        if self.filter_frame.winfo_viewable():
            self.filter_frame.pack_forget()
            return

        for widget in self.filter_frame.winfo_children():
            widget.destroy()

        self.filter_frame.pack(fill="x", padx=10, pady=(10, 5))

        if column == 'stt':
            return

        filter_label = ctk.CTkLabel(self.filter_frame, text=f"Lọc cột '{self.headers[column]}':")
        filter_label.pack(side="left", padx=(15, 10), pady=10)

        unique_values = get_unique_values(self.data_manager.df, column)
        unique_values = sorted([str(v) for v in unique_values])

        if len(unique_values) > 20:
            filter_entry = ctk.CTkEntry(self.filter_frame, placeholder_text=f"Nhập giá trị {self.headers[column]}...")
            filter_entry.pack(side="left", padx=(0, 10), pady=10)
            filter_entry.bind("<KeyRelease>", lambda e: self.apply_text_filter(column, filter_entry.get()))
        else:
            filter_var = tk.StringVar(value="-- Tất cả --")
            filter_values = ["-- Tất cả --"] + unique_values

            filter_menu = ctk.CTkOptionMenu(self.filter_frame, values=filter_values,
                                          variable=filter_var,
                                          command=lambda val: self.apply_option_filter(column, val))
            filter_menu.pack(side="left", padx=(0, 10), pady=10)

        close_filter_btn = ctk.CTkButton(self.filter_frame, text="Đóng",
                                       command=self.close_filter,
                                       width=60)
        close_filter_btn.pack(side="right", padx=(10, 15), pady=10)

        reset_filter_btn = ctk.CTkButton(self.filter_frame, text="Reset",
                                       command=lambda: self.reset_column_filter(column),
                                       width=60)
        reset_filter_btn.pack(side="right", padx=(0, 10), pady=10)

    def close_filter(self):
        """Ẩn khung bộ lọc cột"""
        if hasattr(self, 'filter_frame'):
            self.filter_frame.pack_forget()

    def apply_text_filter(self, column, filter_text):
        """Áp dụng filter dạng text"""
        if not filter_text.strip():
            if column in self.data_manager.column_filters:
                del self.data_manager.column_filters[column]
        else:
            self.data_manager.column_filters[column] = filter_text.strip().lower()

        self.data_manager.apply_filters()
        self.refresh_table()

    def apply_option_filter(self, column, selected_value):
        """Áp dụng filter dạng option menu"""
        if selected_value == "-- Tất cả --":
            if column in self.data_manager.column_filters:
                del self.data_manager.column_filters[column]
        else:
            self.data_manager.column_filters[column] = selected_value

        self.data_manager.apply_filters()
        self.refresh_table()

    def reset_column_filter(self, column):
        """Reset filter cho một cột"""
        if column in self.data_manager.column_filters:
            del self.data_manager.column_filters[column]
        self.data_manager.apply_filters()
        self.refresh_table()

    def refresh_table(self):
        """Làm mới hiển thị bảng dữ liệu"""
        start_time = time.time()
        if not hasattr(self, 'tree') or self.tree is None or self.data_manager.filtered_df.empty:
            return

        delete_start = time.time()
        for item in self.tree.get_children():
            self.tree.delete(item)
        delete_time = time.time() - delete_start
        print(f"Delete time: {delete_time:.4f}s")

        insert_start = time.time()
        for idx, (_, row) in enumerate(self.data_manager.filtered_df.iterrows(), 1):
            values = [str(idx)]
            for col in self.show_cols[1:]:
                if col in self.data_manager.filtered_df.columns:
                    val = row[col]
                    formatted_val = format_display_value(val, col)
                    values.append(formatted_val)
                else:
                    values.append("")
            self.tree.insert("", "end", values=values)
        insert_time = time.time() - insert_start
        print(f"Insert time: {insert_time:.4f}s")

        if hasattr(self, 'title_label'):
            total = len(self.data_manager.df)
            filtered = len(self.data_manager.filtered_df)
            self.title_label.configure(text=f"Danh sách nhân viên ({filtered} / {total} người)")

        if hasattr(self, 'stats_label'):
            filtered = len(self.data_manager.filtered_df)
            self.stats_label.configure(text=f"Hiển thị: {filtered} nhân viên")

        total_time = time.time() - start_time
        print(f"Total refresh time: {total_time:.4f}s")

    def refresh_all(self):
        """Làm mới toàn bộ dữ liệu"""
        self.data_manager.reset_filters()
        self.refresh_table()
        if hasattr(self, 'filter_frame'):
            self.filter_frame.pack_forget()

    def handle_export(self, selected_format):
        """Xử lý lựa chọn định dạng xuất"""
        if self.is_exporting or selected_format == "Chọn định dạng xuất":
            return

        self.is_exporting = True
        try:
            success, message = self.data_manager.export_data(selected_format)
            if success:
                messagebox.showinfo("Thành công", message)
            else:
                messagebox.showerror("Lỗi", message)
        finally:
            self.is_exporting = False
            if self.export_var:
                self.export_var.set("Chọn định dạng xuất")

    def run(self):
        """Khởi động vòng lặp chính"""
        self.root.mainloop()