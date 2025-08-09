# fail2ban_dashboard/log_parser.py

import re
import pandas as pd
import geoip2.database
import os
import warnings
from datetime import date
from utils import get_country_emoji

warnings.simplefilter(action='ignore', category=FutureWarning)

def parse_fail2ban_log(log_file, jail_name):
    print(f"Step 1: Parsing log file '{log_file}' for jail '{jail_name}'...")
    ban_pattern = re.compile(r"fail2ban\.actions\s+\[\d+\]:\s+NOTICE\s+\[{}\]\s+Ban\s+([\d\.]+)".format(re.escape(jail_name)))
    today_str = date.today().strftime("%Y-%m-%d")
    banned_ips = []
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if today_str in line:
                match = ban_pattern.search(line)
                if match:
                    banned_ips.append(match.group(1))
    print(f"   - Found {len(banned_ips)} ban events for today.")
    return banned_ips

def geolocate_ips(ip_list, city_db_path, asn_db_path):
    print("Step 2: Geolocating IPs...")
    unique_ips = sorted(list(set(ip_list)))
    print(f"   - Processing {len(unique_ips)} unique IPs.")
    ip_data = []
    with geoip2.database.Reader(city_db_path, locales=['zh-CN']) as city_reader, \
         geoip2.database.Reader(asn_db_path) as asn_reader:
        for ip in unique_ips:
            try:
                city_info = city_reader.city(ip)
                asn_info = asn_reader.asn(ip)
                if city_info.country.name is None or city_info.location.latitude is None:
                    continue
                ip_data.append({
                    'ip': ip, 'country': city_info.country.name, 'country_code': city_info.country.iso_code,
                    'city': city_info.city.name or '未知', 'latitude': city_info.location.latitude,
                    'longitude': city_info.location.longitude,
                    'asn': f"AS{asn_info.autonomous_system_number} {asn_info.autonomous_system_organization}"
                })
            except geoip2.errors.AddressNotFoundError:
                continue
    return pd.DataFrame(ip_data)

def aggregate_data(all_ips, geo_df):
    print("Step 3: Aggregating data for dashboard...")
    if geo_df.empty: return None
    events_df = pd.DataFrame(all_ips, columns=['ip'])
    full_data = pd.merge(events_df, geo_df, on='ip', how='inner')
    country_agg = full_data.groupby(['country', 'country_code']).agg(
        total_bans=('ip', 'count'), unique_ips=('ip', lambda x: x.nunique())
    ).reset_index().sort_values('total_bans', ascending=False)
    asn_agg = full_data.groupby('asn').agg(
        total_bans=('ip', 'count')
    ).reset_index().sort_values('total_bans', ascending=False)
    map_data_intermediate = pd.merge(
        country_agg, geo_df[['country', 'latitude', 'longitude']].drop_duplicates(subset=['country']),
        on='country', how='left'
    )
    map_data_cleaned = map_data_intermediate.dropna(subset=['latitude', 'longitude'])
    map_data_cleaned['emoji'] = map_data_cleaned['country_code'].apply(get_country_emoji)
    map_data_cleaned['display_name'] = map_data_cleaned['emoji'] + ' ' + map_data_cleaned['country']
    map_data_final = map_data_cleaned.rename(columns={'country': '国家/地区', 'total_bans': '总封禁次数', 'unique_ips': '独立IP数'})
    asn_agg_final = asn_agg.rename(columns={'asn': '机构/ISP (ASN)', 'total_bans': '封禁次数'})
    
    # --- 新增的调试代码 ---
    print("\n" + "="*20 + " BACKEND DEBUG START " + "="*20)
    print("Data being prepared for the map:")
    if map_data_final.empty:
        print("!!! WARNING: The final map data DataFrame is EMPTY. No map can be drawn.")
    else:
        # 打印DataFrame的结构信息和前几行
        map_data_final.info()
        print(map_data_final.head())
    print("="*20 + " BACKEND DEBUG END " + "="*22 + "\n")
    # --- 调试代码结束 ---

    print("   - Aggregation complete.")
    return {
        "map_data": map_data_final.to_dict(orient='records'),
        "country_table": map_data_final.head(10)[['display_name', '总封禁次数']].to_dict(orient='records'),
        "asn_table": asn_agg_final.head(10).to_dict(orient='records'),
    }

def generate_report_data(config):
    print("\n----- Starting Data Generation Process -----")
    try:
        log_file = config['Paths']['log_file']
        jail_name = config['Settings']['jail_name']
        city_db = config['Paths']['geoip_city_db']
        asn_db = config['Paths']['geoip_asn_db']
        for path_key, path_val in [('log_file', log_file), ('city_db', city_db), ('asn_db', asn_db)]:
            if not os.path.exists(path_val):
                raise FileNotFoundError(f"Required file '{path_key}' not found at: {path_val}")
        all_banned_ips = parse_fail2ban_log(log_file, jail_name)
        if not all_banned_ips: return None
        geo_df = geolocate_ips(all_banned_ips, city_db, asn_db)
        if geo_df.empty: return None
        final_data = aggregate_data(all_banned_ips, geo_df)
        print("----- Data Generation Complete -----")
        return final_data
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in log_parser: {e}")
        raise