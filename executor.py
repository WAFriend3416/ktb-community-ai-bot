"""
Playwright 기반 실행 엔진
FR1: 클릭 후보 수집
"""

from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import asyncio
import json
from pathlib import Path

from heuristics import Clickable, Heuristics


class Executor:
    """AI 에이전트 실행 엔진"""

    def __init__(self, profile_id: str, profile_config: Dict[str, Any]):
        self.profile_id = profile_id
        self.profile_config = profile_config

        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

        self.heuristics = Heuristics()

        # 세션 경로
        self.session_dir = Path(f"profiles/{profile_id}")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / "session.json"

    async def init_browser(self, headless: bool = False) -> None:
        """브라우저 초기화 (FR1)"""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(headless=headless)

        # 세션 복원 또는 새 컨텍스트
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            self.context = await self.browser.new_context(
                storage_state=session_data
            )
        else:
            self.context = await self.browser.new_context()

        self.page = await self.context.new_page()

    async def save_session(self) -> None:
        """세션 저장 (FR1)"""
        if self.context:
            session_data = await self.context.storage_state()
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

    async def collect_clickables(self) -> List[Clickable]:
        """
        클릭 가능한 UI 요소 수집 (FR1)
        버튼/링크/submit 메타데이터 수집
        """
        if not self.page:
            return []

        # JavaScript로 클릭 가능 요소 수집
        js_code = """
        () => {
            const elements = [];
            const selectors = [
                'button:not([disabled])',
                'a[href]',
                'input[type=submit]',
                '[role=button]'
            ];

            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0 &&
                                     window.getComputedStyle(el).visibility !== 'hidden';

                    elements.push({
                        selector: sel + ':nth-of-type(' + (idx + 1) + ')',
                        text: el.innerText?.trim() || el.textContent?.trim() || '',
                        href: el.href || null,
                        role: el.getAttribute('role') || null,
                        is_visible: isVisible,
                        tag_name: el.tagName.toLowerCase()
                    });
                });
            });

            return elements;
        }
        """

        raw_elements = await self.page.evaluate(js_code)

        # Clickable 객체로 변환
        clickables = []
        for elem in raw_elements:
            clickables.append(Clickable(
                selector=elem['selector'],
                text=elem['text'],
                href=elem['href'],
                role=elem['role'],
                is_visible=elem['is_visible'],
                tag_name=elem['tag_name']
            ))

        return clickables

    async def check_login_status(self) -> bool:
        """
        로그인 상태 확인 (FR11)
        1단계: 간단한 로그아웃 버튼 존재 여부만 확인
        """
        if not self.page:
            return False

        # 로그아웃 버튼 텍스트 패턴
        logout_patterns = self.heuristics.keywords['cta_patterns']['logout']['text']

        for pattern in logout_patterns:
            try:
                locator = self.page.get_by_text(pattern, exact=False)
                count = await locator.count()
                if count > 0:
                    return True
            except:
                continue

        return False

    async def navigate(self, url: str) -> None:
        """페이지 이동"""
        if self.page:
            await self.page.goto(url, wait_until='networkidle')

    async def close(self) -> None:
        """브라우저 종료"""
        await self.save_session()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
