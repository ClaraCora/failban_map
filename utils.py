# fail2ban_dashboard/utils.py

def get_country_emoji(country_code):
    """
    根据ISO 3166-1 alpha-2国家代码返回对应的国旗emoji。
    例如: 'CN' -> '🇨🇳'
    
    Args:
        country_code (str): 两个字母的国家代码。

    Returns:
        str: 对应的国旗emoji字符串，如果代码无效则返回空字符串。
    """
    if not isinstance(country_code, str) or len(country_code) != 2:
        return ""
    
    # 利用Unicode中区域指示符号的偏移量计算
    # 'A' (U+0041) -> Regional Indicator Symbol Letter A (U+1F1E6)
    # 每个字母加上偏移量即可得到对应的emoji字符
    offset = 0x1F1E6 - ord('A')
    emoji = chr(ord(country_code[0].upper()) + offset) + chr(ord(country_code[1].upper()) + offset)
    return emoji