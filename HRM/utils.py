"""
Các hàm tiện ích cho ứng dụng HRM Employee Manager

Bao gồm định dạng dữ liệu, tìm kiếm, và các hàm hỗ trợ khác.
"""

import pandas as pd
from thefuzz import fuzz


def format_display_value(val, col):
    """Format giá trị để hiển thị dễ đọc hơn"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""

    if isinstance(val, dict):
        if col == 'profile':
            # Hiển thị các trường chính của profile
            address = val.get('address', '')
            marital = val.get('marital', '')
            pob = val.get('pob', '')
            nationality = val.get('nationality', '')
            return f"Address: {address}, Marital: {marital}, POB: {pob}, Nationality: {nationality}"
        elif col == 'bank':
            # Hiển thị thông tin ngân hàng
            number = val.get('number', '')
            name = val.get('name', '')
            return f"Number: {number}, Name: {name}"
        elif col == 'form':
            # Hiển thị các trường có giá trị của form
            items = [f"{k}: {v}" for k, v in val.items() if v not in [None, '', ' ']]
            return ', '.join(items)
        else:
            # Dict khác, hiển thị dạng key: value
            items = [f"{k}: {v}" for k, v in val.items() if v not in [None, '', ' ']]
            return ', '.join(items)
    elif isinstance(val, list):
        if col == 'form':
            # Form là list của dicts, hiển thị name: value
            items = []
            for item in val:
                if isinstance(item, dict):
                    name = item.get('name', '')
                    display_val = item.get('display', item.get('value', ''))
                    if name and display_val:
                        items.append(f"{name}: {display_val}")
            return ', '.join(items)
        else:
            # List khác, hiển thị dạng string
            return str(val)
    else:
        return str(val)


def fuzzy_search_dataframe(df, search_text, columns, threshold=60):
    """Thực hiện tìm kiếm fuzzy trên DataFrame"""
    if not search_text or df.empty:
        return df

    mask = pd.Series([False] * len(df))

    for i, (_, row) in enumerate(df.iterrows()):
        for col in columns:
            if col in df.columns and pd.notna(row[col]):
                similarity = fuzz.partial_ratio(search_text.lower(), str(row[col]).lower())
                if similarity >= threshold:
                    mask.iloc[i] = True
                    break

    return df[mask]


def apply_column_filters(df, filters):
    """Áp dụng bộ lọc cột lên DataFrame"""
    if df.empty:
        return df

    temp_df = df.copy()

    for column, filter_value in filters.items():
        if isinstance(filter_value, str) and len(filter_value) > 0 and column in temp_df.columns:
            mask = temp_df[column].astype(str).str.lower().str.contains(filter_value, na=False, regex=False)
            temp_df = temp_df[mask]

    return temp_df


def get_unique_values(df, column):
    """Lấy giá trị duy nhất cho cột, xử lý unhashable types"""
    if df.empty or column not in df.columns:
        return []

    try:
        unique_values = df[column].dropna().unique()
    except TypeError:
        # Handle unhashable types
        unique_values = pd.Series([str(v) for v in df[column].dropna()]).unique()

    return sorted([str(v) for v in unique_values])


def process_employee_data(employees):
    """Xử lý dữ liệu nhân viên từ API"""
    df = pd.DataFrame(employees)

    # Trích xuất và định dạng các trường cụ thể
    df['email'] = df.apply(lambda x: x.get('email'), axis=1)
    df['phone'] = df.apply(lambda x: x.get('phone'), axis=1)
    df['dob'] = df.apply(
        lambda x: f"{x.get('dob_day')}/{x.get('dob_month')}/{x.get('dob_year')}",
        axis=1
    )
    df['position'] = df.apply(lambda x: x.get('title'), axis=1)
    df['bank_account'] = df.apply(
        lambda x: x.get('bank', {}).get('number'), axis=1
    )
    df['bank_name'] = df.apply(
        lambda x: x.get('bank', {}).get('name'), axis=1
    )

    # Thêm cột STT
    df.reset_index(drop=True, inplace=True)
    df.insert(0, 'stt', range(1, len(df) + 1))

    return df