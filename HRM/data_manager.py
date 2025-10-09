"""
Quản lý dữ liệu cho ứng dụng HRM Employee Manager

Bao gồm các chức năng gọi API, xử lý dữ liệu và xuất dữ liệu.
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv
from .config import API_URL, API_PAGE, API_LIMIT
from .utils import process_employee_data


class DataManager:
    """Quản lý dữ liệu nhân viên"""

    def __init__(self):
        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()
        self.column_filters = {}
        self.search_text = ""

        # Tải biến môi trường
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)

    def fetch_employees(self, api_key):
        """Lấy dữ liệu nhân viên từ API"""
        try:
            payload = {
                "access_token": api_key,
                "page": API_PAGE,
                "limit": API_LIMIT
            }

            response = requests.post(API_URL, data=payload)

            if response.status_code == 200:
                data = response.json()

                if data and 'employees' in data:
                    employees = data['employees']
                    if employees:
                        self.df = process_employee_data(employees)
                        self.filtered_df = self.df.copy()
                        return len(self.df), None
                    else:
                        return 0, "Danh sách nhân viên trống!"
                else:
                    return 0, "Không tìm thấy dữ liệu nhân viên!"
            else:
                return 0, f"API trả về lỗi: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return 0, f"Không thể kết nối đến API: {str(e)}"
        except Exception as e:
            return 0, f"Đã xảy ra lỗi: {str(e)}"

    def apply_filters(self):
        """Áp dụng tất cả bộ lọc"""
        from .utils import fuzzy_search_dataframe, apply_column_filters

        if self.df.empty:
            self.filtered_df = pd.DataFrame()
            return

        # Áp dụng tìm kiếm
        if self.search_text:
            search_columns = ['name', 'email', 'phone', 'code', 'position']
            self.filtered_df = fuzzy_search_dataframe(self.df, self.search_text, search_columns)
        else:
            self.filtered_df = self.df.copy()

        # Áp dụng bộ lọc cột
        self.filtered_df = apply_column_filters(self.filtered_df, self.column_filters)

    def reset_filters(self):
        """Đặt lại tất cả bộ lọc"""
        self.column_filters = {}
        self.search_text = ""
        self.filtered_df = self.df.copy()

    def export_data(self, format_type, filename=None):
        """Xuất dữ liệu"""
        if self.filtered_df.empty:
            return False, "Không có dữ liệu để xuất!"

        if filename is None:
            base_name = "employees"
        else:
            base_name = filename

        try:
            if format_type.upper() == "CSV":
                file_path = f"{base_name}.csv"
                self.filtered_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif format_type.upper() == "EXCEL":
                file_path = f"{base_name}.xlsx"
                self.filtered_df.to_excel(file_path, index=False)
            elif format_type.upper() == "JSON":
                file_path = f"{base_name}.json"
                self.filtered_df.to_json(file_path, orient='records', indent=4, force_ascii=False)
            else:
                return False, f"Định dạng {format_type} không được hỗ trợ!"

            return True, f"Đã xuất {len(self.filtered_df)} nhân viên ra file {file_path}"

        except Exception as e:
            return False, f"Không thể xuất file: {str(e)}"