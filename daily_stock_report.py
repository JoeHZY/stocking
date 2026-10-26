import requests
import json
import efinance as ef
import pandas as pd
from datetime import datetime

# 叔叔的 10 只标的池
STOCKS = [
    {"code": "600900", "name": "长江电力", "market": "A"},
    {"code": "000831", "name": "中国稀土", "market": "A"},
    {"code": "300059", "name": "东方财富", "market": "A"},
    {"code": "002202", "name": "金风科技", "market": "A"},
    {"code": "02208",  "name": "金风科技HK", "market": "HK"},
    {"code": "601899", "name": "紫金矿业", "market": "A"},
    {"code": "601112", "name": "振石股份", "market": "A"},
    {"code": "600406", "name": "国电南瑞", "market": "A"},
    {"code": "600089", "name": "特变电工", "market": "A"},
    {"code": "300014", "name": "亿纬锂能", "market": "A"}
]

def fetch_market_data():
    stock_codes = [s["code"] for s in STOCKS]
    try:
        # 批量拉取实时/最新收盘指标
        df = ef.stock.get_latest_quote(stock_codes)
    except Exception as e:
        print(f"行情拉取异常: {e}")
        return None

    report_list = []
    # 筛选并标准化数据
    for s in STOCKS:
        matched = df[df['代码'] == s["code"]]
        if not matched.empty:
            row = matched.iloc[0]
            report_list.append({
                "名称": s["name"],
                "代码": s["code"],
                "最新价": row.get("最新价", "N/A"),
                "涨跌幅(%)": row.get("涨跌幅", "N/A"),
                "成交额": f"{round(float(row.get('成交额', 0)) / 1e8, 2)}亿" if row.get('成交额') else "N/A",
                "换手率(%)": row.get("换手率", "N/A"),
                "振幅(%)": row.get("振幅", "N/A"),
                "主力净流入": f"{round(float(row.get('主力净流入', 0)) / 1e4, 2)}万" if row.get('主力净流入') else "0"
            })
    return pd.DataFrame(report_list)

def analyze_with_ollama(data_text):
    prompt = f"""你是一名拥有15年经验的资深买方投资顾问。以下是用户自选的10只重点跟踪股票的最新收盘数据：

{data_text}

请为投资者（长辈）生成一份结构清晰、语气沉稳客观的【每日盘后研报】：
1. 【大势与自选概览】：一句话总结这10只股票今日整体表现（涨跌分布、核心风向板块，如新能源/电力/顺周期资源）。
2. 【重点标的异动速评】：挑出今日波动较大（涨跌幅明显、放量或主力资金大幅出入）的 2~3 只标的，进行重点提炼与逻辑推测。
3. 【自选股速览表格】：按涨跌幅整理出清晰的清单，附带一句话短评。
4. 【客观风险提示】：指出当前自选池中需留意的潜在风险点（如部分新股/高弹性标的换手偏高、顺周期板块海外扰动等）。

要求：
- 严禁任何绝对化断言，不主观喊单买卖；
- 语言简练，字体排版清晰大方，适合在手机上阅读。
"""
    # 请求本地 Ollama 服务
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-coder:32b",
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        return resp.json().get("response", "模型无响应")
    except Exception as e:
        return f"调用本地模型分析失败: {e}"

if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"正在拉取 {today_str} 自选股盘后数据...")
    df_data = fetch_market_data()
    
    if df_data is not None and not df_data.empty:
        data_summary = df_data.to_markdown(index=False)
        print("行情拉取完成，正在调起 Qwen-32B 深度分析...")
        analysis_result = analyze_with_ollama(data_summary)
        
        # 保存到本地 Markdown 文件
        output_path = f"/Users/joe/Desktop/股票每日简报_{today_str}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
            
        print(f"\n✅ 简报生成成功！已保存至桌面: {output_path}\n")
        print(analysis_result)
    else:
        print("未获取到有效的股票行情数据。")
