"""
휴리스틱 기반 UI 요소 스코어링 모듈
FR2: CTA/Curiosity 스코어링, 상위 후보 선택
"""

from typing import List, Dict, Any, Optional, Literal, Tuple
import re
import json
from pathlib import Path


# 데이터 구조 (LLD 기반)
class Clickable:
    """클릭 가능한 UI 요소"""
    def __init__(
        self,
        selector: str,
        text: str = "",
        href: Optional[str] = None,
        role: Optional[str] = None,
        is_visible: bool = True,
        tag_name: str = ""
    ):
        self.selector = selector
        self.text = text
        self.href = href
        self.role = role
        self.is_visible = is_visible
        self.tag_name = tag_name


class ScoredAction:
    """스코어링된 액션"""
    def __init__(
        self,
        clickable: Clickable,
        total_score: float,
        intent: Literal["cta", "curiosity"],
        breakdown: Optional[Dict[str, float]] = None
    ):
        self.clickable = clickable
        self.total_score = total_score
        self.intent = intent
        self.breakdown = breakdown or {}


class Heuristics:
    """휴리스틱 스코어링 엔진"""

    def __init__(self, keywords_path: str = "config/keywords.json"):
        with open(keywords_path, 'r', encoding='utf-8') as f:
            self.keywords = json.load(f)

        self.cta_patterns = self.keywords['cta_patterns']
        self.curiosity_patterns = self.keywords['curiosity_patterns']

    def score_cta(
        self,
        clickable: Clickable,
        is_logged_in: bool
    ) -> Tuple[float, str]:
        """
        CTA 스코어링 (FR2)
        Returns: (score, cta_type)
        """
        score = 0.0
        matched_cta = ""

        # 로그인 상태 필터링
        if is_logged_in:
            skip_ctas = ['signup', 'login']
            priority_ctas = ['write_post', 'comment', 'logout']
        else:
            skip_ctas = ['logout', 'write_post', 'comment']
            priority_ctas = ['signup', 'login']

        for cta_type, patterns in self.cta_patterns.items():
            if cta_type in skip_ctas:
                continue

            # 텍스트 매칭
            text_lower = self.normalize_text(clickable.text)
            for keyword in patterns['text']:
                if self.normalize_text(keyword) in text_lower:
                    score += 10.0
                    matched_cta = cta_type
                    break

            # URL 매칭
            if clickable.href:
                href_lower = clickable.href.lower()
                for url_pattern in patterns['url']:
                    if url_pattern.lower() in href_lower:
                        score += 8.0
                        matched_cta = cta_type
                        break

            # 우선순위 CTA 가중치
            if matched_cta == cta_type and cta_type in priority_ctas:
                score *= 1.5

        # Role 속성 가중치
        if clickable.role in ['button', 'link']:
            score += 2.0

        # Submit 버튼
        if clickable.tag_name == 'button' or 'submit' in clickable.selector.lower():
            score += 3.0

        return (score, matched_cta)

    def score_curiosity(self, clickable: Clickable) -> float:
        """
        Curiosity 스코어링 (FR2)
        """
        score = 0.0

        for pattern_type, pattern_data in self.curiosity_patterns.items():
            weight = pattern_data.get('weight', 1.0)

            # URL 패턴
            if clickable.href:
                href_lower = clickable.href.lower()
                for url_pattern in pattern_data.get('url', []):
                    if url_pattern.lower() in href_lower:
                        score += weight * 5.0
                        break

            # 텍스트 패턴
            text_lower = self.normalize_text(clickable.text)
            for text_pattern in pattern_data.get('text', []):
                if self.normalize_text(text_pattern) in text_lower:
                    score += weight * 3.0
                    break

        return score

    def select_top_candidates(
        self,
        scored_actions: List[ScoredAction],
        top_n: int = 3
    ) -> Optional[ScoredAction]:
        """
        상위 N개 중 확률적 선택 (FR2)
        """
        if not scored_actions:
            return None

        # 점수 내림차순 정렬
        sorted_actions = sorted(
            scored_actions,
            key=lambda x: x.total_score,
            reverse=True
        )

        # 상위 N개
        top_candidates = sorted_actions[:top_n]

        # 점수 0인 경우 제외
        top_candidates = [a for a in top_candidates if a.total_score > 0]

        if not top_candidates:
            return None

        # 확률적 선택 (점수 비례)
        import random
        total = sum(a.total_score for a in top_candidates)
        if total == 0:
            return random.choice(top_candidates)

        rand = random.uniform(0, total)
        cumulative = 0.0
        for action in top_candidates:
            cumulative += action.total_score
            if rand <= cumulative:
                return action

        return top_candidates[0]

    @staticmethod
    def normalize_text(text: str) -> str:
        """텍스트 정규화"""
        return re.sub(r'\s+', ' ', text.strip().lower())

    @staticmethod
    def loop_key(clickable: Clickable) -> str:
        """루프 방지용 고유 키 (FR5)"""
        if clickable.href:
            return f"href:{clickable.href}"
        return f"text:{Heuristics.normalize_text(clickable.text)}"
