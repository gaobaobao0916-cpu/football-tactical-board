#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球战术板 - 双源数据抓取器 v2.0
第1层: 雷速体育 (leisu.com) - 赛程/队名/联赛/时间/状态  (自动)
第2层: football-data.org API - 比分/赛果                 (自动)
第3层: 盘口/xG 手动补录                                     (手动)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import sys
import os
import argparse
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional

# ===================== 配置 =====================
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "match_data.json")
REQUEST_TIMEOUT = 15
RETRY_COUNT = 3

# football-data.org 免费API (无需注册即可使用基础端点)
FOOTBALL_DATA_URL = "https://api.football-data.org/v4"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def safe_request(url: str, encoding: str = None, headers_extra: dict = None) -> Optional[str]:
    """带重试的请求"""
    h = HEADERS.copy()
    if headers_extra:
        h.update(headers_extra)
    
    for attempt in range(RETRY_COUNT):
        try:
            resp = requests.get(url, headers=h, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.text  # 返回原始文本，让调用方 json.loads
            if encoding:
                resp.encoding = encoding
            elif resp.apparent_encoding:
                resp.encoding = resp.apparent_encoding
            return resp.text
        except requests.RequestException as e:
            print(f"  [{attempt+1}/{RETRY_COUNT}] 请求失败: {e}")
            if attempt < RETRY_COUNT - 1:
                time.sleep(2)
    return None


# ===================== 第1层: 雷速体育赛程抓取 =====================

def scrape_leisu() -> List[Dict]:
    """
    抓取雷速体育 (leisu.com) 首页赛程数据
    使用已验证的CSS选择器: div.match-label → .home a / .away a / .eventname a / .time span
    
    状态类名:
      - .status.start = 未开赛
      - .status.live / .status.playing = 进行中
      - .status.finish / .status.end = 已结束
    """
    print(f"\n=== 雷速体育: 抓取赛程数据 ===")
    
    url = "https://www.leisu.com/"
    html = safe_request(url)
    
    if not html:
        print("  ❌ 雷速体育无法连接")
        return []
    
    soup = BeautifulSoup(html, "lxml")
    matches = []
    
    containers = soup.select("div.match-label")
    print(f"  找到 {len(containers)} 个比赛容器")
    
    for c in containers:
        try:
            # === 核心元素 (已验证选择器) ===
            time_el = c.select_one(".time .timecolor") or c.select_one(".time span")
            league_el = c.select_one(".eventname a")
            home_el = c.select_one(".home a")
            away_el = c.select_one(".away a")
            status_el = c.select_one(".status")
            
            time_txt = time_el.get_text(strip=True) if time_el else ""
            league_txt = league_el.get_text(strip=True) if league_el else ""
            home_txt = home_el.get_text(strip=True) if home_el else ""
            away_txt = away_el.get_text(strip=True) if away_el else ""
            
            if not home_txt or not away_txt:
                continue
            
            # === 比分 (进行中/已结束才有) ===
            # 比分可能在 .score 或 .home-score/.away-score 中
            score = ""
            score_el = c.select_one(".score") or c.select_one("[class*='score']")
            if score_el:
                score_txt = score_el.get_text(strip=True)
                # 过滤掉非比分文本（如 "VS"、"-"、空）
                if score_txt and re.match(r"\d+\s*[-:]\s*\d+", score_txt):
                    score = re.sub(r"\s+", "", score_txt)
            
            # === 状态判断 ===
            status = "未开赛"
            if status_el:
                status_cls = " ".join(status_el.get("class", [])).lower()
                if any(kw in status_cls for kw in ["live", "playing", "ongoing", "inplay"]):
                    status = "进行中"
                elif any(kw in status_cls for kw in ["finish", "end", "finished", "over"]):
                    status = "已结束"
            
            # === 提取比赛ID (从链接中提取，备用) ===
            match_id = ""
            match_link = c.select_one("a[href*='detail-'], a[href*='/match/']")
            if match_link:
                href = match_link.get("href", "")
                id_match = re.search(r"detail-(\d+)", href) or re.search(r"/match/(\d+)", href)
                if id_match:
                    match_id = id_match.group(1)
            
            match = {
                "source": "leisu",
                "match_id": match_id,
                "league": league_txt,
                "time": time_txt,
                "home_team": home_txt,
                "away_team": away_txt,
                "score": score,
                "status": status,
                "home_shots": "",
                "away_shots": "",
                "home_shots_on_target": "",
                "away_shots_on_target": "",
                "home_danger_attacks": "",
                "away_danger_attacks": "",
            }
            matches.append(match)
        except Exception as e:
            continue
    
    # 分类统计
    live = sum(1 for m in matches if m["status"] == "进行中")
    finished = sum(1 for m in matches if m["status"] == "已结束")
    pending = sum(1 for m in matches if m["status"] == "未开赛")
    
    print(f"  ✅ 雷速体育: {len(matches)} 场 (进行中:{live} 已结束:{finished} 未开赛:{pending})")
    for m in matches[:8]:
        extra = f" [{m['match_id']}]" if m['match_id'] else ""
        print(f"     {m['home_team']} vs {m['away_team']} | {m['league']} | {m['time']} | {m['score'] or '-'} | {m['status']}{extra}")
    if len(matches) > 8:
        print(f"     ... 还有 {len(matches)-8} 场")
    
    return matches


# ===================== 第2层: football-data.org API =====================

def scrape_football_data() -> List[Dict]:
    """
    通过 football-data.org 免费API获取当天比赛的比分数据
    无需注册即可使用 (有限额)
    """
    print(f"\n=== football-data.org: 获取比分数据 ===")
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    matches = []
    
    # 尝试获取当天比赛 (免费API有限制，可能只返回部分联赛)
    url = f"{FOOTBALL_DATA_URL}/matches?dateFrom={today}&dateTo={tomorrow}"
    
    try:
        resp_text = safe_request(url, headers_extra={"Accept": "application/json"})
        if resp_text:
            data = json.loads(resp_text)
            
            if "matches" in data:
                for m in data["matches"]:
                    home = m.get("homeTeam", {}).get("name", "")
                    away = m.get("awayTeam", {}).get("name", "")
                    
                    if not home or not away:
                        continue
                    
                    score_data = m.get("score", {}).get("fullTime", {})
                    home_score = score_data.get("home", "")
                    away_score = score_data.get("away", "")
                    
                    score = ""
                    if home_score is not None and away_score is not None:
                        score = f"{home_score}-{away_score}"
                    
                    competition = m.get("competition", {}).get("name", "")
                    utc_time = m.get("utcDate", "")[:16].replace("T", " ")
                    
                    status_map = {
                        "SCHEDULED": "未开赛",
                        "LIVE": "进行中",
                        "IN_PLAY": "进行中",
                        "PAUSED": "进行中",
                        "FINISHED": "已结束",
                        "AWARDED": "已结束",
                        "POSTPONED": "延期",
                        "CANCELLED": "取消",
                    }
                    status = status_map.get(m.get("status", ""), "未知")
                    
                    matches.append({
                        "source": "football_data",
                        "league": competition,
                        "time": utc_time,
                        "home_team": home,
                        "away_team": away,
                        "score": score,
                        "status": status,
                        "home_shots": "",
                        "away_shots": "",
                        "home_shots_on_target": "",
                        "away_shots_on_target": "",
                        "home_danger_attacks": "",
                        "away_danger_attacks": "",
                    })
    except Exception as e:
        print(f"  ⚠️ football-data.org API 异常: {e} (可能需要注册或超限额)")
    
    print(f"  ✅ football-data.org: {len(matches)} 场比赛")
    return matches


# ===================== 数据合并与去重 =====================

def merge_all_data(leisu_matches: List[Dict], api_matches: List[Dict]) -> List[Dict]:
    """
    合并雷速和API数据，按队名匹配，优先使用API的比分
    """
    if not leisu_matches and not api_matches:
        return []
    
    merged = list(leisu_matches)
    
    for api_m in api_matches:
        api_home = api_m.get("home_team", "").strip().lower()
        api_away = api_m.get("away_team", "").strip().lower()
        
        matched = False
        for m in merged:
            m_home = m.get("home_team", "").strip().lower()
            m_away = m.get("away_team", "").strip().lower()
            
            # 模糊匹配
            if (api_home and m_home and api_away and m_away):
                if api_home == m_home and api_away == m_away:
                    matched = True
                elif api_home in m_home or m_home in api_home:
                    if api_away in m_away or m_away in api_away:
                        matched = True
            
            if matched:
                # API的比分优先
                if not m.get("score") and api_m.get("score"):
                    m["score"] = api_m["score"]
                if not m.get("league") and api_m.get("league"):
                    m["league"] = api_m["league"]
                if m.get("status") == "未开赛" and api_m.get("status") != "未开赛":
                    m["status"] = api_m["status"]
                break
        
        if not matched:
            merged.append(api_m)
    
    print(f"\n📊 合并结果: {len(merged)} 场比赛 (雷速: {len(leisu_matches)}, API: {len(api_matches)})")
    return merged


# ===================== 格式化输出 =====================

def format_for_tactical_board(matches: List[Dict]) -> List[Dict]:
    """格式化为战术板可导入的JSON格式"""
    output = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for m in matches:
        output.append({
            "match_time": m.get("time", today),
            "league": m.get("league", ""),
            "home_team": m.get("home_team", ""),
            "away_team": m.get("away_team", ""),
            "live_score": m.get("score", ""),
            "live_asian_handicap": m.get("live_asian_handicap", ""),
            "live_over_under": m.get("live_over_under", ""),
            "shots_ratio": m.get("shots_ratio", ""),
            "shots_on_target_ratio": m.get("shots_on_target_ratio", ""),
            "danger_attacks_ratio": m.get("danger_attacks_ratio", ""),
            "home_xg": m.get("home_xg", ""),
            "away_xg": m.get("away_xg", ""),
            "match_status": m.get("status", "未开赛"),
            "notes": f"来源: {m.get('source', 'unknown')}",
        })
    
    return output


def save_output(matches: List[Dict], output_file: str = None):
    """保存到JSON文件"""
    if output_file is None:
        output_file = OUTPUT_FILE
    
    formatted = format_for_tactical_board(matches)
    
    output = {
        "fetch_time": datetime.now().isoformat(),
        "fetch_time_display": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match_count": len(formatted),
        "matches": formatted,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    live = sum(1 for m in formatted if m["match_status"] == "进行中")
    finished = sum(1 for m in formatted if m["match_status"] == "已结束")
    pending = sum(1 for m in formatted if m["match_status"] == "未开赛")
    has_score = sum(1 for m in formatted if m["live_score"])
    has_odds = sum(1 for m in formatted if m["live_asian_handicap"])
    has_xg = sum(1 for m in formatted if m["home_xg"])
    
    print(f"\n{'='*60}")
    print(f"💾 数据已保存: {output_file}")
    print(f"   共 {len(formatted)} 场比赛")
    print(f"   进行中: {live} | 已结束: {finished} | 未开赛: {pending}")
    print(f"   有比分: {has_score} | 有盘口: {has_odds} | 有xG: {has_xg}")
    
    missing = []
    for m in formatted:
        if m["match_status"] == "进行中":
            if not m["live_asian_handicap"]:
                missing.append(f"  {m['home_team']} vs {m['away_team']}: 盘口")
            if not m["home_xg"]:
                missing.append(f"  {m['home_team']} vs {m['away_team']}: xG")
    
    if missing:
        print(f"\n⚠️  需手动补录 ({len(missing)} 项)")
    print("=" * 60)


# ===================== 主入口 =====================

def main():
    parser = argparse.ArgumentParser(description="足球战术板数据抓取器 v2.0")
    parser.add_argument("--source", "-s", choices=["leisu", "api", "both"], default="both", help="数据源")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  足球战术板 - 数据抓取器 v2.0")
    print("  雷速体育 (赛程) + football-data.org (比分)")
    print("=" * 60)
    
    all_matches = []
    
    if args.source in ("leisu", "both"):
        leisu = scrape_leisu()
        all_matches = leisu
    
    if args.source in ("api", "both"):
        api_data = scrape_football_data()
        all_matches = merge_all_data(all_matches, api_data)
    
    save_output(all_matches, args.output)
    
    print("\n📋 下一步:")
    print("  1. 打开战术板 → 点「导入数据」→ 选择 match_data.json")
    print("  2. 手动补录: 盘口(让球/大小球) + xG 预期进球")
    print("  3. 条件格式自动触发 (压制不进球 / 数据均衡)")


if __name__ == "__main__":
    main()
