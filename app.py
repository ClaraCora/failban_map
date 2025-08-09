# fail2ban_dashboard/app.py

from flask import Flask, render_template, jsonify, request
import configparser
import json
import os
import log_parser # 导入我们自己的数据处理模块

app = Flask(__name__)

# 加载配置
config = configparser.ConfigParser()
config.read('config.ini')
JSON_OUTPUT_FILE = config['Paths']['output_json']

@app.route('/')
def index():
    """渲染主网页"""
    return render_template('index.html')

@app.route('/data')
def get_data():
    """提供最新的报告数据，并包含视图配置"""
    if not os.path.exists(JSON_OUTPUT_FILE):
        return jsonify({"error": "Data file not found. Please refresh data first."}), 404
    
    with open(JSON_OUTPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # --- 核心修改：将服务器和视图配置一起传给前端 ---
    data['server_config'] = {
        'lat': config.getfloat('Settings', 'server_latitude'),
        'lon': config.getfloat('Settings', 'server_longitude'),
        'name': config.get('Settings', 'server_name'),
        # 读取并传递 default_view 配置，如果不存在则默认为 'native'
        'default_view': config.get('Settings', 'default_view', fallback='native')
    }
    return jsonify(data)

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """触发数据刷新流程"""
    try:
        report_data = log_parser.generate_report_data(config)
        
        if report_data:
            os.makedirs(os.path.dirname(JSON_OUTPUT_FILE), exist_ok=True)
            with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
            return jsonify({"status": "success", "message": "Data refreshed successfully."})
        else:
            return jsonify({"status": "noop", "message": "No new data to process."})

    except Exception as e:
        print(f"Error during data refresh: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 当使用 Gunicorn 运行时，这个 block 不会被执行，但保留它用于直接运行脚本进行调试
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)