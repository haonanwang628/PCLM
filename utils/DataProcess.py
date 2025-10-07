# 最后delete 合并到dataset
import pandas as pd
import json
import os

# 设置 Excel 文件路径
excel_path = r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\orgin\Data Analysis - First Cycle - RQ1 - Final.xlsx"  # 👈 请替换为你的 Excel 文件名
output_json = r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\processed\First Cycle - RQ1.json"

# === 加载 Excel 文件和参与者工作表 ===
xls = pd.ExcelFile(excel_path)
participant_sheets = [s for s in xls.sheet_names if s.lower().startswith("participant")]

# === 收集所有展开后的记录 ===
expanded_rows = []

for sheet in participant_sheets:
    try:
        # header=2 即第三行为列名，Data chunk 在第5列，Code 在第6列
        df = pd.read_excel(xls, sheet_name=sheet, header=2)

        data_chunk_col = df.columns[4]  # Unnamed: 4
        code_col = df.columns[5]  # Unnamed: 5

        # 向下填充 chunk 并去除空值
        df[data_chunk_col] = df[data_chunk_col].fillna(method="ffill")
        df = df[[data_chunk_col, code_col]].dropna()

        for _, row in df.iterrows():
            chunk = str(row[data_chunk_col]).strip()
            if chunk == "Data chunk":
                continue
            code_block = str(row[code_col]).strip()
            if chunk and code_block:
                for code in code_block.split("\n"):
                    code = code.strip()
                    if code:
                        expanded_rows.append({
                            "participant": sheet,
                            "data_chunk": chunk,
                            "code": code
                        })

    except Exception as e:
        print(f"⚠️ 跳过 {sheet}: {e}")
        continue

# === 分组聚合 code 列 ===
df_expanded = pd.DataFrame(expanded_rows)
grouped = (
    df_expanded
    .groupby(["participant", "data_chunk"])["code"]
    .apply(list)
    .reset_index()
)

# === 导出为 JSON 文件 ===
records = grouped.to_dict(orient="records")

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 已导出 JSON 文件，共 {len(records)} 条记录")
print(f"📄 文件路径：{output_json}")
