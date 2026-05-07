#!/usr/bin/env python3
"""Generate weekly or monthly work reports from several local git repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent
WEEKLY_XLSX_TEMPLATE = Path("/Users/oncechen/Downloads/04_27-04_30 前端上周工作总结.xlsx")

DEPARTMENTS = {
    "RT": {
        "吉祥坊(JXF)": {
            "contacts": ("Oswin", "Musk"),
            "repos": [
                "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main",
                "/Users/oncechen/IdeaProjects/jxf_web_static_vue_dev",
            ],
        },
        "UED": {
            "contacts": ("Roger", "Lelisu"),
            "repos": [
                "/Users/oncechen/IdeaProjects/c_ued",
                "/Users/oncechen/IdeaProjects/ued_web_static_vue",
                "/Users/oncechen/IdeaProjects/ued_web_vue",
            ],
        },
        "TQ(Sportone)": {
            "contacts": ("Angemi", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/c_sportone/web"],
        },
    },
    "MT": {
        "走地皇(RB88)": {
            "contacts": ("Belly", "Ayea"),
            "repos": [
                "/Users/oncechen/IdeaProjects/rb88_web_vue_main",
                "/Users/oncechen/IdeaProjects/rb88_web_vue_dev",
            ],
        },
        "QY框架": {
            "contacts": ("Jairo", "-"),
            "repos": [
                "/Users/oncechen/IdeaProjects/qy_web_static_vue",
                "/Users/oncechen/IdeaProjects/qy_web_vue",
            ],
        },
        "QM框架(PT777_web_static_vue)": {
            "contacts": ("Jyue", "-"),
            "repos": [
                "/Users/oncechen/IdeaProjects/pt777_web_static_vue",
                "/Users/oncechen/IdeaProjects/pt777_web_vue",
            ],
        },
        "QY": {
            "contacts": ("AaronY", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/c_qy"],
        },
        "QM(PT777)": {
            "contacts": ("Avram", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/c_pt777"],
        },
        "L8": {
            "contacts": ("Papa", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/c_long8/web"],
        },
        "LW": {
            "contacts": ("Mason", "-"),
            "repos": [
                "/Users/oncechen/IdeaProjects/e68_web_static_vue",
                "/Users/oncechen/IdeaProjects/e68_web_vue",
            ],
        },
    },
    "非业务": {
        "94Chat": {
            "contacts": ("Nolan", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/site-dolphin"],
        },
        "飞鱼": {
            "contacts": ("Nolan", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/feiyu-site"],
        },
        "优客服": {
            "contacts": ("Nolan", "-"),
            "repos": ["/Users/oncechen/IdeaProjects/youkefu-site"],
        },
    },
}

LEGACY_DEPARTMENTS = {
    "MT部门（long8、pt777、qy、e68、rb88）": {
        "long8": ["/Users/oncechen/IdeaProjects/c_long8/web"],
        "pt777": [
            "/Users/oncechen/IdeaProjects/c_pt777",
            "/Users/oncechen/IdeaProjects/pt777_web_static_vue",
            "/Users/oncechen/IdeaProjects/pt777_web_vue",
        ],
        "qy": [
            "/Users/oncechen/IdeaProjects/c_qy",
            "/Users/oncechen/IdeaProjects/qy_web_static_vue",
            "/Users/oncechen/IdeaProjects/qy_web_vue",
        ],
        "e68": [
            "/Users/oncechen/IdeaProjects/e68_web_static_vue",
            "/Users/oncechen/IdeaProjects/e68_web_vue",
        ],
        "rb88": [
            "/Users/oncechen/IdeaProjects/rb88_web_vue_main",
            "/Users/oncechen/IdeaProjects/rb88_web_vue_dev",
        ],
    },
    "RT部门（sportone、ued、jxf）": {
        "sportone": ["/Users/oncechen/IdeaProjects/c_sportone/web"],
        "ued": [
            "/Users/oncechen/IdeaProjects/c_ued",
            "/Users/oncechen/IdeaProjects/ued_web_static_vue",
            "/Users/oncechen/IdeaProjects/ued_web_vue",
        ],
        "jxf": [
            "/Users/oncechen/IdeaProjects/jxf_web_static_vue_main",
            "/Users/oncechen/IdeaProjects/jxf_web_static_vue_dev",
        ],
    },
}

DOMAIN_RULES = [
    ("提款/账户", ["提款", "取款", "提现", "绑卡", "银行卡", "虚拟币", "支付密码", "账户绑定", "提款账户"]),
    ("支付/存款", ["存款", "充值", "支付", "支付宝", "c2c", "uploademail", "二维码", "凭证", "钱包", "金流", "v4存款", "推荐钱包", "usdt"]),
    ("游戏/赛事", ["世界杯", "worldcup", "world cup", "赛事", "投注", "赔率", "盘口", "红单", "ob", "直播", "聊天室", "游戏", "老虎机", "pt游戏", "pgpt", "熊猫体育", "jdb", "真人"]),
    ("活动专题", ["端午", "五一", "劳动节", "5月专题", "五月专题", "专题", "活动", "mayday", "dragonboat", "festival", "奖池", "排行榜", "赞助", "首单包赔"]),
    ("代理/合营", ["代理", "合营", "agent", "代存", "推广链接", "财务报表", "会员输赢", "提款申请"]),
    ("登录/注册", ["登录", "登入", "注册", "找回", "解锁", "密码", "推荐码", "账号", "小写"]),
    ("APP/H5/下载", ["app", "下载", "h5", "鸿蒙", "ios", "跳转", "打开", "viewport", "safari"]),
    ("VIP/福利", ["福利", "vip", "筹码", "救援金", "返水", "返利", "优惠券", "生日礼金", "会员日"]),
    ("客服/通知", ["客服", "帮助中心", "专属客服", "短信", "速讯通", "麦讯通", "通知", "公告"]),
    ("工程配置", ["ci", "main.yml", "dev.yml", "vuejs config", "vite.config", "项目瘦身", "sdk", "域名", "filter.java"]),
    ("文案/样式", ["文案", "样式", "图片", "素材", "ui", "跑版", "错字", "logo", "banner", "图标"]),
]

NEW_KEYWORDS = [
    "新增", "新建", "加入", "添加", "初版", "上线", "接入", "feat", "feature", "new",
    "改版", "专题", "教程", "活动", "页面", "聊天室", "v4", "鸿蒙",
]

MAINTENANCE_KEYWORDS = [
    "修复", "修正", "调整", "优化", "更新", "修改", "更换", "补齐", "兼容", "配置",
    "下架", "删除", "清理", "fix", "bug", "chore", "merge", "冲突", "错误", "问题",
]

AUTHOR_ALIASES = {
    "AaronY": ["aarony"],
    "Angemi": ["angemi"],
    "Avram": ["avram"],
    "Ayea": ["ayea"],
    "Belly": ["belly"],
    "Jairo": ["jairo"],
    "Jyue": ["jyue"],
    "Lelisu": ["lelisu"],
    "Mason": ["mason"],
    "Musk": ["musk"],
    "Nolan": ["nolan"],
    "Oswin": ["oswin"],
    "Papa": ["papa"],
    "Roger": ["roger"],
}

NOISE_PATTERNS = [
    re.compile(r"^merge\b", re.I),
    re.compile(r"codex init", re.I),
    re.compile(r"^测试"),
    re.compile(r"^删除测试代码"),
]


@dataclass
class Commit:
    date: str
    sha: str
    author: str
    subject: str
    repo: str
    files: list[str] = field(default_factory=list)


@dataclass
class KpiResult:
    grade: str
    score: int
    effective_commits: int
    new_count: int
    maintenance_count: int
    domains: list[str]
    reason: str


def run_git_log(repo: str, since: str, until: str) -> list[Commit]:
    if not (Path(repo) / ".git").exists():
        return []

    fmt = "%x1e%ad%x1f%h%x1f%an%x1f%s"
    cmd = [
        "git",
        "-C",
        repo,
        "log",
        f"--since={since}",
        f"--until={until}",
        "--date=short",
        f"--pretty=format:{fmt}",
        "--name-only",
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    commits: list[Commit] = []
    repo_name = Path(repo).name
    for block in result.stdout.split("\x1e"):
        block = block.strip("\n")
        if not block:
            continue
        header, *file_lines = block.splitlines()
        parts = header.split("\x1f")
        if len(parts) != 4:
            continue
        commit = Commit(parts[0], parts[1], parts[2], parts[3], repo_name)
        commit.files.extend(line.strip() for line in file_lines if line.strip())
        commits.append(commit)
    return commits


def period_dates(period: str, today: dt.date) -> tuple[str, str, str]:
    if period == "week":
        start = today - dt.timedelta(days=today.weekday())
        label = f"{start:%Y-%m-%d} 至 {today:%Y-%m-%d}"
        return start.isoformat(), (today + dt.timedelta(days=1)).isoformat(), label
    if period == "last-week":
        this_week = today - dt.timedelta(days=today.weekday())
        start = this_week - dt.timedelta(days=7)
        end = this_week - dt.timedelta(days=1)
        label = f"{start:%Y-%m-%d} 至 {end:%Y-%m-%d}"
        return start.isoformat(), this_week.isoformat(), label
    if period == "month":
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        end_inclusive = next_month - dt.timedelta(days=1)
        label = f"{start:%Y-%m-%d} 至 {min(today, end_inclusive):%Y-%m-%d}"
        return start.isoformat(), next_month.isoformat(), label
    if period == "last-month":
        this_month = today.replace(day=1)
        end = this_month - dt.timedelta(days=1)
        start = end.replace(day=1)
        label = f"{start:%Y-%m-%d} 至 {end:%Y-%m-%d}"
        return start.isoformat(), this_month.isoformat(), label
    raise ValueError(f"Unsupported period: {period}")


def last_month_final_week_dates(today: dt.date) -> tuple[str, str, str]:
    this_month = today.replace(day=1)
    end = this_month - dt.timedelta(days=1)
    start = end - dt.timedelta(days=end.weekday())
    label = f"{start:%Y-%m-%d} 至 {end:%Y-%m-%d}"
    return start.isoformat(), this_month.isoformat(), label


def month_text_from_since(since: str) -> str:
    date_value = dt.date.fromisoformat(since)
    return f"{date_value:%Y年%m月}"


def chinese_month_name_from_since(since: str) -> str:
    names = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
    date_value = dt.date.fromisoformat(since)
    return f"{names[date_value.month - 1]}月份"


def title_with_period(title: str, since: str, label: str) -> str:
    if "工作总结" in title:
        return title
    if "月" in title:
        return f"{title}（{month_text_from_since(since)}，{label}）"
    return f"{title}（{label}）"


def compact_date_range(since: str, until: str, separator: str = "/") -> str:
    start = dt.date.fromisoformat(since)
    end = dt.date.fromisoformat(until) - dt.timedelta(days=1)
    return f"{start:%m}{separator}{start:%d}-{end:%m}{separator}{end:%d}"


def weekly_summary_title(since: str, until: str, current: bool = False) -> str:
    week_text = "本周" if current else "上周"
    start = dt.date.fromisoformat(since)
    end = dt.date.fromisoformat(until) - dt.timedelta(days=1)
    return f"{start:%m%d}_{end:%m%d}_前端{week_text}工作总结"


def is_noise(subject: str) -> bool:
    return any(pattern.search(subject.strip()) for pattern in NOISE_PATTERNS)


def normalize_author(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def author_matches(contact: str, author: str) -> bool:
    if contact == "-":
        return False
    normalized_author = normalize_author(author)
    aliases = AUTHOR_ALIASES.get(contact, [contact])
    return any(normalize_author(alias) in normalized_author for alias in aliases)


def normalize_subject(subject: str) -> str:
    text = subject.strip()
    text = re.sub(r"^(fix|new|feature|bug)[:：]\s*", "", text, flags=re.I)
    text = re.sub(r"^BUG-\d+", "", text, flags=re.I).strip(" -：:")
    text = re.sub(r"\s+", " ", text)
    return text or subject.strip()


def categorize(commit: Commit) -> str:
    haystack = " ".join([commit.subject, *commit.files]).lower()
    for category, keywords in DOMAIN_RULES:
        if any(keyword.lower() in haystack for keyword in keywords):
            return category
    return "其他"


def change_type(commit: Commit) -> str:
    subject = commit.subject.lower()
    has_new = any(keyword.lower() in subject for keyword in NEW_KEYWORDS)
    has_maintenance = any(keyword.lower() in subject for keyword in MAINTENANCE_KEYWORDS)
    if has_new and not has_maintenance:
        return "新增需求"
    if has_new and any(keyword in subject for keyword in ["新增", "新建", "加入", "添加", "初版", "上线", "接入", "feat", "feature", "new"]):
        return "新增需求"
    if has_maintenance:
        return "维护需求"
    return "维护需求"


def demand_phrase(commit: Commit) -> str:
    subject = normalize_subject(commit.subject)
    if subject in {"优化", "日常维护", "页面调整", "更新接口", "更新css"} and commit.files:
        first = commit.files[0].lower()
        if "worldcup" in first:
            return "世界杯专题优化"
        if "agent" in first:
            return "代理中心优化"
        if "deposit" in first or "recharge" in first:
            return "存款/充值流程优化"
    return subject


def unique_ordered(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def summarize_group(commits: list[Commit]) -> dict[str, dict[str, list[str]]]:
    grouped: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for commit in commits:
        if is_noise(commit.subject):
            continue
        grouped[change_type(commit)][categorize(commit)].append(demand_phrase(commit))
    return {
        type_name: {domain: unique_ordered(values) for domain, values in domains.items()}
        for type_name, domains in grouped.items()
    }


def filtered_commits(commits: list[Commit]) -> list[Commit]:
    return [commit for commit in commits if not is_noise(commit.subject)]


def dedupe_commits(commits: list[Commit]) -> list[Commit]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Commit] = []
    for commit in filtered_commits(commits):
        key = (commit.date, normalize_author(commit.author), normalize_subject(commit.subject).lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(commit)
    return out


def kpi_grade(score: int) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 80:
        return "A-"
    if score >= 75:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "B-"
    if score >= 40:
        return "C"
    return "D"


def kpi_standard(grade: str) -> str:
    standards = {
        "N/A": "本周期未查询到有效提交，暂不评分，需结合实际任务分配人工确认",
        "A+": "超出制定计划目标，刷新团队或项目新标",
        "A": "达成制定计划目标",
        "A-": "达成部分制定目标，仍有提升及努力空间",
        "B+": "未完全达成目标，但产出积极，受外在因素影响较多",
        "B": "未完全达成目标，有主动产出，但方法和聚焦度仍需改善",
        "B-": "未达成目标，产出偏少或覆盖面不足",
        "C": "对项目产生明显负面影响或有效产出极低",
        "D": "严重违规、职务侵占或其他恶性事件",
    }
    return standards[grade]


RANK_GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C", "D"]
GRADE_SCORES = {
    "A+": 100,
    "A": 92,
    "A-": 85,
    "B+": 78,
    "B": 72,
    "B-": 65,
    "C": 50,
    "D": 30,
}


def grade_for_rank(rank_index: int) -> str:
    if rank_index < len(RANK_GRADES):
        return RANK_GRADES[rank_index]
    return "D"


def evaluate_ranked_kpis(owner_commits: dict[str, list[Commit]]) -> dict[str, KpiResult]:
    counts: dict[str, int] = {}
    deduped_by_owner: dict[str, list[Commit]] = {}
    for owner, commits in owner_commits.items():
        deduped = dedupe_commits(commits)
        deduped_by_owner[owner] = deduped
        counts[owner] = len(deduped)

    ranked_counts = sorted(set(counts.values()), reverse=True)
    grade_by_count = {
        count: grade_for_rank(index)
        for index, count in enumerate(ranked_counts)
    }

    results: dict[str, KpiResult] = {}
    for owner, deduped in deduped_by_owner.items():
        count = counts[owner]
        summary = summarize_group(deduped)
        new_count = sum(1 for commit in deduped if change_type(commit) == "新增需求")
        maintenance_count = max(count - new_count, 0)
        domains = sorted({domain for domains in summary.values() for domain in domains})
        grade = grade_by_count[count]
        reason = (
            f"组内去重有效提交 {count} 个，新增 {new_count} 个，维护 {maintenance_count} 个，"
            f"覆盖 {len(domains)} 个业务域"
        )
        results[owner] = KpiResult(grade, GRADE_SCORES[grade], count, new_count, maintenance_count, domains, reason)
    return results


def evaluate_kpi(commits: list[Commit], summary: dict[str, dict[str, list[str]]]) -> KpiResult:
    effective = filtered_commits(commits)
    effective_count = len(effective)
    new_count = sum(1 for commit in effective if change_type(commit) == "新增需求")
    maintenance_count = max(effective_count - new_count, 0)
    domains = sorted({domain for domains in summary.values() for domain in domains})
    core_domains = {"游戏/赛事", "支付/存款", "提款/账户", "活动专题", "代理/合营"}
    core_count = len(core_domains.intersection(domains))

    if effective_count == 0:
        return KpiResult("N/A", 0, 0, 0, 0, [], "本周期未查询到有效提交")

    score = 50
    score += min(effective_count, 15)
    score += min(int(len(domains) * 2.5), 15)
    score += min(int(new_count * 1.5), 8)
    score += min(int(core_count * 2.5), 10)
    if effective_count >= 15 and len(domains) >= 4:
        score += 5
    if score < 60:
        score = 60
    score = max(0, min(score, 100))

    reason = (
        f"有效提交 {effective_count} 个，新增 {new_count} 个，维护 {maintenance_count} 个，"
        f"覆盖 {len(domains)} 个业务域"
    )
    if core_count:
        reason += f"，其中核心域 {core_count} 个"
    return KpiResult(kpi_grade(score), score, effective_count, new_count, maintenance_count, domains, reason)


def period_need_title(report_name: str) -> str:
    month_match = re.search(r"([一二三四五六七八九十]+月份)", report_name)
    if month_match:
        return f"{month_match.group(1)}需求："
    if "上周" in report_name:
        return "上周需求："
    if "上个月" in report_name:
        return "上个月需求："
    if "本周" in report_name:
        return "本周需求："
    if "本月" in report_name:
        return "本月需求："
    return "需求："


def summary_lines(summary: dict[str, dict[str, list[str]]]) -> list[str]:
    lines: list[str] = []
    for type_name in ("新增需求", "维护需求"):
        domains = summary.get(type_name)
        if not domains:
            continue
        lines.append(f"- **{type_name}**")
        for domain in sorted(domains):
            phrases = domains[domain]
            joined = "、".join(phrases[:8])
            if len(phrases) > 8:
                joined += "等"
            lines.append(f"  - {domain}：{joined}。")
    return lines


def summary_text(summary: dict[str, dict[str, list[str]]], limit: int = 8) -> str:
    items: list[str] = []
    for type_name in ("新增需求", "维护需求"):
        domains = summary.get(type_name)
        if not domains:
            continue
        for domain in sorted(domains):
            phrases = domains[domain]
            joined = "、".join(phrases[:limit])
            if len(phrases) > limit:
                joined += "等"
            type_label = type_name.replace("需求", "")
            items.append(f"{type_label}（{domain}）：{joined}")
    if not items:
        return "1.日常维护"
    return "\n".join(f"{index}. {item}。" for index, item in enumerate(items, 1))


def weekly_plan_text(summary: dict[str, dict[str, list[str]]]) -> str:
    domains = sorted({domain for typed in summary.values() for domain in typed})
    if not domains:
        return "1.日常维护"
    focus = "、".join(domains[:4])
    return f"1. 持续跟进{focus}相关需求。\n2. 处理禅道 BUG、线上反馈与日常维护。"


def weekly_excel_rows(departments: dict, since: str, until: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for department_name, projects in departments.items():
        if department_name == "RT":
            continue
        first_project = True
        section_name = "综合/体育" if department_name == "MT" else "市场"
        for project_name, project_meta in projects.items():
            commits: list[Commit] = []
            for repo in project_meta.get("repos", []):
                if (Path(repo) / ".git").exists():
                    commits.extend(run_git_log(repo, since, until))
            summary = summarize_group(commits)
            rows.append((
                section_name if first_project else "",
                project_name,
                summary_text(summary),
                weekly_plan_text(summary),
            ))
            first_project = False
    return rows


def render_report(
    departments: dict,
    since: str,
    until: str,
    label: str,
    report_name: str,
) -> str:
    lines = [
        f"# {title_with_period(report_name, since, label)}",
        "",
        f"- 统计范围：`{since}` 到 `{until}`（git 查询 until 为开区间）",
        "- 说明：已过滤 Merge、明显测试类提交；需求归纳为基于 git 记录的自动整理。",
        "",
    ]

    project_cache: dict[str, tuple[list[Commit], list[str], tuple[str, str]]] = {}

    for department_name, projects in departments.items():
        for project_name, project_meta in projects.items():
            contacts = project_meta.get("contacts", ("-", "-"))
            repos = project_meta.get("repos", [])
            commits: list[Commit] = []
            missing: list[str] = []
            for repo in repos:
                if not (Path(repo) / ".git").exists():
                    missing.append(repo)
                    continue
                commits.extend(run_git_log(repo, since, until))
            commits.sort(key=lambda item: (item.date, item.sha), reverse=True)
            project_cache[project_name] = (commits, missing, contacts)

    for department_name, projects in departments.items():
        lines.extend([f"## {department_name}", ""])
        for project_name, project_meta in projects.items():
            commits, missing, contacts = project_cache[project_name]

            lines.extend([f"### {project_name}", ""])
            if missing:
                lines.append("未找到仓库：")
                lines.extend(f"- `{path}`" for path in missing)
                lines.append("")
            if not commits:
                lines.extend(["本周期没有查询到提交。", ""])
                continue

            summary = summarize_group(commits)
            lines.append(period_need_title(report_name))
            lines.extend(summary_lines(summary))
            lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def collect_kpi_data(
    departments: dict,
    since: str,
    until: str,
) -> tuple[dict[str, dict[str, list[Commit]]], dict[str, dict[str, list[str]]], dict[str, dict[str, list[str]]]]:
    department_owner_commits: dict[str, dict[str, list[Commit]]] = defaultdict(lambda: defaultdict(list))
    department_owner_projects: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    department_unmatched_contacts: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for department_name, projects in departments.items():
        for project_name, project_meta in projects.items():
            contacts = project_meta.get("contacts", ("-", "-"))
            repos = project_meta.get("repos", [])
            commits: list[Commit] = []
            for repo in repos:
                if not (Path(repo) / ".git").exists():
                    continue
                commits.extend(run_git_log(repo, since, until))
            for contact in contacts:
                if contact == "-":
                    continue
                matched = [commit for commit in commits if author_matches(contact, commit.author)]
                if matched:
                    department_owner_commits[department_name][contact].extend(matched)
                    department_owner_projects[department_name][contact].append(project_name)
                else:
                    department_unmatched_contacts[department_name][contact].append(project_name)

    return department_owner_commits, department_owner_projects, department_unmatched_contacts


def kpi_section_lines(departments: dict, since: str, until: str, label: str, section_name: str) -> list[str]:
    owner_commits, owner_projects, unmatched_contacts = collect_kpi_data(departments, since, until)
    lines = [
        f"## {title_with_period(section_name, since, label)}",
        "",
        f"- 统计范围：`{since}` 到 `{until}`（git 查询 until 为开区间）",
        "",
    ]

    for department_name in ("RT", "MT"):
        lines.extend([f"### {department_name}", ""])
        ranked = evaluate_ranked_kpis(owner_commits.get(department_name, {}))
        owners = sorted(ranked, key=lambda owner: (-ranked[owner].effective_commits, owner.lower()))
        if not owners:
            lines.append("本周期未匹配到可评分负责人。")
        for owner in owners:
            kpi = ranked[owner]
            projects = "、".join(owner_projects[department_name][owner])
            lines.append(f"- **{owner}**：{kpi.grade}（{kpi.score}/100）。负责项目：{projects}。{kpi_standard(kpi.grade)}；{kpi.reason}。")
        notes = []
        department_unmatched = unmatched_contacts.get(department_name, {})
        department_projects = owner_projects.get(department_name, {})
        for contact in sorted(department_unmatched):
            if contact in department_projects:
                continue
            notes.append(f"{contact}（{ '、'.join(department_unmatched[contact]) }）")
        if notes:
            lines.append("未匹配到 git author，暂不评分：" + "；".join(notes) + "。")
        lines.append("")

    other_departments = [name for name in departments if name not in {"RT", "MT"}]
    for department_name in other_departments:
        lines.extend([f"### {department_name}", ""])
        ranked = evaluate_ranked_kpis(owner_commits.get(department_name, {}))
        owners = sorted(ranked, key=lambda owner: (-ranked[owner].effective_commits, owner.lower()))
        if not owners:
            lines.append("本周期未匹配到可评分负责人。")
        for owner in owners:
            kpi = ranked[owner]
            projects = "、".join(owner_projects[department_name][owner])
            lines.append(f"- **{owner}**：{kpi.grade}（{kpi.score}/100）。负责项目：{projects}。{kpi_standard(kpi.grade)}；{kpi.reason}。")
        notes = []
        department_unmatched = unmatched_contacts.get(department_name, {})
        department_projects = owner_projects.get(department_name, {})
        for contact in sorted(department_unmatched):
            if contact in department_projects:
                continue
            notes.append(f"{contact}（{ '、'.join(department_unmatched[contact]) }）")
        if notes:
            lines.append("未匹配到 git author，暂不评分：" + "；".join(notes) + "。")
        lines.append("")

    return lines


def render_kpi_report(departments: dict, periods: list[tuple[str, str, str, str]], title: str = "KPI评分") -> str:
    lines = [
        f"# {title}",
        "",
        "- 说明：KPI 评分基于 git author 与负责人姓名匹配后的提交记录自动评估。",
        "- KPI 规则：RT 与 MT 分开计算；组内按去重后的有效提交数排序，最多 A+、第二 A、第三 A-、第四 B+，依次为 B、B-、C、D；同提交数并列同等级。",
        "- 评级说明：A+ 超出计划目标；A 达成计划目标；A- 达成部分目标仍有提升空间；B+/B/B- 为未完全达成但产出程度不同；C/D 需结合实际负面影响或违规事实判断，git 记录仅作参考。",
        "",
    ]
    for section_name, since, until, label in periods:
        lines.extend(kpi_section_lines(departments, since, until, label, section_name))
    return "\n".join(lines).rstrip() + "\n"


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def markdown_to_html(markdown: str, title: str) -> str:
    body: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            body.append("<div class='space'></div>")
            continue
        if line.startswith("#### "):
            body.append(f"<h4>{inline_markdown(line[5:])}</h4>")
        elif line.startswith("### "):
            body.append(f"<h3>{inline_markdown(line[4:])}</h3>")
        elif line.startswith("## "):
            body.append(f"<h2>{inline_markdown(line[3:])}</h2>")
        elif line.startswith("# "):
            body.append(f"<h1>{inline_markdown(line[2:])}</h1>")
        elif line.startswith("  - "):
            body.append(f"<div class='bullet bullet-sub'>- {inline_markdown(line[4:])}</div>")
        elif line.startswith("- "):
            body.append(f"<div class='bullet'>- {inline_markdown(line[2:])}</div>")
        else:
            body.append(f"<p>{inline_markdown(line)}</p>")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 14mm 13mm; }}
    body {{
      color: #1f2933;
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB",
        "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
      font-size: 11px;
      line-height: 1.55;
    }}
    h1 {{ font-size: 22px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 2px solid #111827; }}
    h2 {{ font-size: 17px; margin: 22px 0 8px; padding: 6px 8px; background: #eef2f7; }}
    h3 {{ font-size: 14px; margin: 16px 0 6px; color: #0f4c81; }}
    h4 {{ font-size: 12px; margin: 10px 0 4px; color: #374151; }}
    p {{ margin: 3px 0; }}
    .bullet {{ margin: 2px 0 2px 12px; text-indent: -10px; }}
    .bullet-sub {{ margin-left: 28px; color: #374151; }}
    .space {{ height: 5px; }}
    code {{ font-family: Menlo, Monaco, Consolas, monospace; font-size: 10px; color: #7c2d12; }}
    strong {{ color: #111827; }}
  </style>
</head>
<body>
{chr(10).join(body)}
</body>
</html>
"""


def find_chrome() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


def write_report_files(markdown: str, output_stem: Path, output_format: str) -> list[str]:
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    md_path = Path(f"{output_stem}.md")
    html_path = Path(f"{output_stem}.html")
    pdf_path = Path(f"{output_stem}.pdf")

    if output_format in {"md", "both", "pdf"}:
        md_path.write_text(markdown, encoding="utf-8")
    if output_format in {"md", "both"}:
        paths.append(os.path.abspath(md_path))
    if output_format in {"pdf", "both"}:
        html_path.write_text(markdown_to_html(markdown, output_stem.name), encoding="utf-8")
        chrome = find_chrome()
        if not chrome:
            raise SystemExit("找不到 Chrome/Chromium，无法自动生成 PDF。已生成 HTML/Markdown。")
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f"PDF 生成失败：{result.stderr or result.stdout}")
        paths.append(os.path.abspath(pdf_path))
    return paths


def set_inline_string(cell: ET.Element, value: str | None) -> None:
    for child in list(cell):
        cell.remove(child)
    cell.attrib.pop("t", None)
    if value is None or value == "":
        return
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, f"{{{XML_MAIN_NS}}}is")
    text = ET.SubElement(inline, f"{{{XML_MAIN_NS}}}t")
    if value != value.strip():
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text.text = value


XML_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", XML_MAIN_NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("mx", "http://schemas.microsoft.com/office/mac/excel/2008/main")
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")
ET.register_namespace("mv", "urn:schemas-microsoft-com:mac:vml")
ET.register_namespace("x14", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main")
ET.register_namespace("x15", "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main")
ET.register_namespace("x14ac", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac")
ET.register_namespace("xm", "http://schemas.microsoft.com/office/excel/2006/main")


def column_name(cell_ref: str) -> str:
    return re.sub(r"\d+", "", cell_ref)


def ensure_row(root: ET.Element, row_index: int) -> ET.Element:
    sheet_data = root.find(f"{{{XML_MAIN_NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("template sheetData not found")
    for row in sheet_data.findall(f"{{{XML_MAIN_NS}}}row"):
        if row.get("r") == str(row_index):
            return row
    row = ET.Element(f"{{{XML_MAIN_NS}}}row", {"r": str(row_index)})
    sheet_data.append(row)
    return row


def ensure_cell(row: ET.Element, cell_ref: str, style: str = "3") -> ET.Element:
    for cell in row.findall(f"{{{XML_MAIN_NS}}}c"):
        if cell.get("r") == cell_ref:
            return cell
    cell = ET.Element(f"{{{XML_MAIN_NS}}}c", {"r": cell_ref, "s": style})
    row.append(cell)
    row[:] = sorted(row, key=lambda c: (int(re.sub(r"\D+", "", c.get("r", "0")) or 0), column_name(c.get("r", ""))))
    return cell


def write_weekly_excel(
    departments: dict,
    since: str,
    until: str,
    output_stem: Path,
    template_path: Path = WEEKLY_XLSX_TEMPLATE,
) -> str | None:
    if not template_path.exists():
        return None

    rows = weekly_excel_rows(departments, since, until)
    output_path = Path(f"{output_stem}.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template_path, "r") as source:
        sheet_xml = source.read("xl/worksheets/sheet1.xml")
        root = ET.fromstring(sheet_xml)

        set_inline_string(ensure_cell(ensure_row(root, 1), "A1", "1"), "WEB组周报汇总")
        set_inline_string(ensure_cell(ensure_row(root, 2), "A2", "3"), "产品")
        set_inline_string(ensure_cell(ensure_row(root, 2), "C2", "3"), "上周总结")
        set_inline_string(ensure_cell(ensure_row(root, 2), "D2", "3"), "本周计划")

        for offset, (department_name, project_name, summary, plan) in enumerate(rows, start=3):
            row = ensure_row(root, offset)
            set_inline_string(ensure_cell(row, f"A{offset}", "3"), department_name)
            set_inline_string(ensure_cell(row, f"B{offset}", "3"), project_name)
            set_inline_string(ensure_cell(row, f"C{offset}", "3"), summary)
            set_inline_string(ensure_cell(row, f"D{offset}", "3"), plan)
            row.set("customHeight", "1")
            row.set("ht", "110")

        for row_index in range(3 + len(rows), 40):
            row = ensure_row(root, row_index)
            for col in ("A", "B", "C", "D"):
                set_inline_string(ensure_cell(row, f"{col}{row_index}", "3"), "")

        updated_sheet = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = updated_sheet if item.filename == "xl/worksheets/sheet1.xml" else source.read(item.filename)
                target.writestr(item, data)

    return os.path.abspath(output_path)


def output_stem_from_arg(output: str) -> Path:
    path = Path(output)
    if path.suffix.lower() in {".pdf", ".md", ".html"}:
        path = path.with_suffix("")
    return path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a git-based work report.")
    parser.add_argument(
        "--period",
        choices=["week", "last-week", "month", "last-month"],
        help="Generate a single demand report for this period. Default without args: last-month demand and last-month KPI PDFs.",
    )
    parser.add_argument("--since", help="Start date, inclusive. Example: 2026-04-01.")
    parser.add_argument("--until", help="End date, exclusive. Example: 2026-05-01.")
    parser.add_argument("--today", help="Override today. Example: 2026-05-07.")
    parser.add_argument("--both", action="store_true", help="Generate both last-week and last-month reports.")
    parser.add_argument("--kpi", action="store_true", help="Generate KPI scoring report. Default KPI period is last-month.")
    parser.add_argument("--format", choices=["pdf", "md", "both"], default="pdf", help="Output format. Default: pdf.")
    parser.add_argument("--output", help="Output path for a single report. Suffix is replaced by selected format.")
    parser.add_argument("--output-dir", default=str(SCRIPT_DIR / "reports"), help="Output directory.")
    parser.add_argument("--stdout", action="store_true", help="Print report to stdout instead of writing a file.")
    return parser.parse_args()


def build_report(period: str, today: dt.date) -> tuple[str, str, str, str]:
    since, until, label = period_dates(period, today)
    month_name = chinese_month_name_from_since(since)
    report_names = {
        "week": weekly_summary_title(since, until, current=True),
        "last-week": weekly_summary_title(since, until),
        "month": "本月工作报告",
        "last-month": f"{month_name}月报",
    }
    report_name = report_names.get(period, "工作报告")
    report = render_report(DEPARTMENTS, since, until, label, report_name)
    return since, until, label, report


def build_kpi_report(today: dt.date, period_keys: list[str] | None = None) -> str:
    last_month_since, _, _ = period_dates("last-month", today)
    last_month_name = chinese_month_name_from_since(last_month_since)
    period_names = {
        "week": "本周KPI评分",
        "last-week": "上周KPI评分",
        "month": "本月KPI评分",
        "last-month": f"{last_month_name}KPI评分",
    }
    periods: list[tuple[str, str, str, str]] = []
    for period in period_keys or ["last-month"]:
        since, until, label = period_dates(period, today)
        periods.append((period_names[period], since, until, label))
    title = "KPI评分" if len(periods) > 1 else f"{periods[0][0]}（{month_text_from_since(periods[0][1])}）"
    return render_kpi_report(DEPARTMENTS, periods, title)


def default_output_stem(period: str, today: dt.date, output_dir: str) -> Path:
    last_month_start = (today.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
    last_month_name = chinese_month_name_from_since(last_month_start.isoformat())
    week_since, week_until, _ = period_dates("week", today)
    last_week_since, last_week_until, _ = period_dates("last-week", today)
    last_month_week_since, last_month_week_until, _ = last_month_final_week_dates(today)
    names = {
        "week": weekly_summary_title(week_since, week_until, current=True),
        "last-week": weekly_summary_title(last_week_since, last_week_until),
        "last-month-week": weekly_summary_title(last_month_week_since, last_month_week_until),
        "month": "本月工作报告",
        "last-month": f"{last_month_name}月报_{last_month_start:%Y年%m月}",
        "kpi": f"{last_month_name}KPI评分_{last_month_start:%Y年%m月}",
    }
    if period == "last-month-week":
        return Path(output_dir) / names[period]
    return Path(output_dir) / f"{names.get(period, '工作报告')}_{today:%Y%m%d}"


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    if args.kpi and not (args.period or args.since or args.until or args.both):
        report = build_kpi_report(today)
        if args.stdout:
            print(report)
            return 0
        output_stem = output_stem_from_arg(args.output) if args.output else default_output_stem("kpi", today, args.output_dir)
        print("\n".join(write_report_files(report, output_stem, args.format)))
        return 0

    if args.both or not (args.period or args.since or args.until or args.kpi):
        outputs: list[str] = []
        rendered: list[str] = []
        if not args.both:
            since, until, label = last_month_final_week_dates(today)
            report = render_report(DEPARTMENTS, since, until, label, weekly_summary_title(since, until))
            weekly_stem = default_output_stem("last-month-week", today, args.output_dir)
            if args.stdout:
                rendered.append(report)
            else:
                outputs.extend(write_report_files(report, weekly_stem, args.format))
                weekly_xlsx = write_weekly_excel(DEPARTMENTS, since, until, weekly_stem)
                if weekly_xlsx:
                    outputs.append(weekly_xlsx)
        report_periods = ("last-week", "last-month") if args.both else ("last-month",)
        for period in report_periods:
            _, _, _, report = build_report(period, today)
            if args.stdout:
                rendered.append(report)
                continue
            outputs.extend(write_report_files(report, default_output_stem(period, today, args.output_dir), args.format))
        kpi_periods = ["last-week", "last-month"] if args.both else ["last-month"]
        kpi_report = build_kpi_report(today, kpi_periods)
        if args.stdout:
            rendered.append(kpi_report)
        else:
            outputs.extend(write_report_files(kpi_report, default_output_stem("kpi", today, args.output_dir), args.format))
        if args.stdout:
            print("\n\n---\n\n".join(rendered))
        else:
            print("\n".join(outputs))
        return 0

    if args.since or args.until:
        if not (args.since and args.until):
            raise SystemExit("--since and --until must be used together.")
        since, until = args.since, args.until
        label = f"{since} 至 {dt.date.fromisoformat(until) - dt.timedelta(days=1):%Y-%m-%d}"
        duration = (dt.date.fromisoformat(until) - dt.date.fromisoformat(since)).days
        report_name = weekly_summary_title(since, until) if duration <= 7 else "工作报告"
        report = render_report(DEPARTMENTS, since, until, label, report_name)
        period = "custom"
    else:
        period = args.period
        _, _, _, report = build_report(args.period, today)

    if args.stdout:
        print(report)
        return 0

    output_stem = output_stem_from_arg(args.output) if args.output else default_output_stem(period, today, args.output_dir)
    print("\n".join(write_report_files(report, output_stem, args.format)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
