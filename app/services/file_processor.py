import pandas as pd
import camelot
import re
import math
import io
import tempfile


def _sanitize_table(df):
    """Convert DataFrame to JSON-safe list of dicts"""
    if df is None or df.empty:
        return []

    df = df.where(pd.notnull(df), None)

    records = df.to_dict(orient="records")

    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, float) and math.isnan(v):
                clean_row[k] = None
            else:
                clean_row[k] = v
        cleaned.append(clean_row)

    return cleaned


def process_excel(file_obj):
    """Process Excel file from file object or path."""
    # file_obj can be a FileStorage object, BytesIO, or file path
    df = pd.read_excel(file_obj)

    balance_column = None

    for col in df.columns:
        if str(col).strip().lower() == "balance":
            balance_column = col
            break

    max_balance = None
    min_balance = None

    if balance_column:
        series = pd.to_numeric(df[balance_column], errors="coerce")
        max_balance = series.max()
        min_balance = series.min()

    if pd.isna(max_balance):
        max_balance = None
    if pd.isna(min_balance):
        min_balance = None

    table = _sanitize_table(df)

    return table, max_balance, min_balance


def process_pdf(file_obj):
    """Process PDF file from file object or path.
    
    Note: Camelot requires a file path, so we use a temporary file
    if a file object is provided.
    """
    # Check if file_obj is a file-like object or a path
    if isinstance(file_obj, str):
        # It's a file path
        tables = camelot.read_pdf(file_obj, pages="all")
    else:
        # It's a file-like object, create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
            file_obj.seek(0)
            tmp_file.write(file_obj.read())
        
        try:
            tables = camelot.read_pdf(tmp_path, pages="all")
        finally:
            # Clean up temp file
            import os
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    balances = []
    final_df = None

    for table in tables:
        df = table.df
        final_df = df

        balance_column = None
        for col in df.columns:
            if df[col].astype(str).str.strip().str.lower().eq("balance").any():
                balance_column = col
                break

        if balance_column:
            for value in df[balance_column]:
                val = str(value).strip().lower()
                if val == "balance":
                    continue

                cleaned = re.sub(r"[^\d.]", "", val)
                if not cleaned:
                    continue

                try:
                    balances.append(float(cleaned))
                except ValueError:
                    pass

    max_balance = max(balances) if balances else None
    min_balance = min(balances) if balances else None

    table = _sanitize_table(final_df)

    return table, max_balance, min_balance
