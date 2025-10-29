"""
메인 엔트리포인트
N개 프로필 동시 실행, 레이트 리미팅, Stop 제어
"""

import asyncio
import os
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
import yaml
from dotenv import load_dotenv

from executor import Executor
from heuristics import Heuristics, ScoredAction


# 환경변수 로드
load_dotenv()


class RateLimiter:
    """레이트 리미터 (FR6)"""

    def __init__(
        self,
        read_rps: int = 1,
        write_qpm: int = 6
    ):
        self.read_rps = read_rps
        self.write_qpm = write_qpm

        self.read_tokens = read_rps
        self.write_tokens = write_qpm

        self.last_read_refill = datetime.now()
        self.last_write_refill = datetime.now()

        self.lock = asyncio.Lock()

    async def acquire_read(self) -> bool:
        """읽기 토큰 획득 (1 RPS)"""
        async with self.lock:
            now = datetime.now()

            # 토큰 리필 (1초마다)
            elapsed = (now - self.last_read_refill).total_seconds()
            if elapsed >= 1.0:
                self.read_tokens = min(self.read_rps, self.read_tokens + int(elapsed))
                self.last_read_refill = now

            if self.read_tokens > 0:
                self.read_tokens -= 1
                return True

            return False

    async def acquire_write(self, actor_id: str) -> bool:
        """쓰기 토큰 획득 (6 QPM)"""
        async with self.lock:
            now = datetime.now()

            # 토큰 리필 (1분마다)
            elapsed = (now - self.last_write_refill).total_seconds()
            if elapsed >= 60.0:
                self.write_tokens = min(self.write_qpm, self.write_tokens + int(elapsed / 60))
                self.last_write_refill = now

            if self.write_tokens > 0:
                self.write_tokens -= 1
                return True

            return False


class StopController:
    """Stop 신호 제어 (FR6)"""

    def __init__(self):
        self.stop_all = asyncio.Event()
        self.stop_actors: Dict[str, asyncio.Event] = {}

    def signal_stop_all(self) -> None:
        """전체 중지"""
        self.stop_all.set()

    def signal_stop_actor(self, actor_id: str) -> None:
        """특정 액터 중지"""
        if actor_id not in self.stop_actors:
            self.stop_actors[actor_id] = asyncio.Event()
        self.stop_actors[actor_id].set()

    def should_stop(self, actor_id: str) -> bool:
        """중지 여부 확인"""
        if self.stop_all.is_set():
            return True

        if actor_id in self.stop_actors and self.stop_actors[actor_id].is_set():
            return True

        return False


class GlobalState:
    """전역 상태"""

    def __init__(self):
        self.rate_limiter = RateLimiter(
            read_rps=int(os.getenv('GLOBAL_READ_RPS', 1)),
            write_qpm=int(os.getenv('GLOBAL_WRITE_QPM', 6))
        )
        self.stop_controller = StopController()
        self.protection_windows: Dict[str, datetime] = {}


async def run_actor(
    actor_id: str,
    profile_config: Dict[str, Any],
    global_state: GlobalState,
    target_url: str
) -> None:
    """
    단일 프로필 실행 루프 (1단계: 기본 탐색만)
    """
    print(f"[{actor_id}] 시작")

    executor = Executor(actor_id, profile_config)
    heuristics = Heuristics()

    try:
        # 브라우저 초기화
        headless = os.getenv('PLAYWRIGHT_HEADLESS', 'false').lower() == 'true'
        await executor.init_browser(headless=headless)

        # 타겟 URL 이동
        print(f"[{actor_id}] {target_url} 이동")
        await executor.navigate(target_url)

        # 간단한 탐색 루프 (1단계)
        max_iterations = 5
        for i in range(max_iterations):
            if global_state.stop_controller.should_stop(actor_id):
                print(f"[{actor_id}] Stop 신호 수신")
                break

            # 레이트 리미팅
            if not await global_state.rate_limiter.acquire_read():
                print(f"[{actor_id}] 레이트 제한 대기")
                await asyncio.sleep(1)
                continue

            # 클릭 요소 수집
            print(f"[{actor_id}] 반복 {i+1}: UI 스캔")
            clickables = await executor.collect_clickables()
            print(f"[{actor_id}] 발견된 요소: {len(clickables)}개")

            # 로그인 상태 확인
            is_logged_in = await executor.check_login_status()
            print(f"[{actor_id}] 로그인 상태: {is_logged_in}")

            # 스코어링
            scored_actions: List[ScoredAction] = []
            for clickable in clickables:
                if not clickable.is_visible:
                    continue

                # CTA 스코어
                cta_score, cta_type = heuristics.score_cta(clickable, is_logged_in)
                if cta_score > 0:
                    scored_actions.append(ScoredAction(
                        clickable=clickable,
                        total_score=cta_score,
                        intent="cta",
                        breakdown={"cta": cta_score, "type": cta_type}
                    ))
                    continue

                # Curiosity 스코어
                curiosity_score = heuristics.score_curiosity(clickable)
                if curiosity_score > 0:
                    scored_actions.append(ScoredAction(
                        clickable=clickable,
                        total_score=curiosity_score,
                        intent="curiosity"
                    ))

            # 상위 후보 선택
            selected = heuristics.select_top_candidates(scored_actions, top_n=3)
            if selected:
                print(f"[{actor_id}] 선택: {selected.intent} - {selected.clickable.text[:50]} (점수: {selected.total_score:.2f})")
            else:
                print(f"[{actor_id}] 선택 가능한 요소 없음")
                break

            # 1단계: 실제 클릭은 하지 않고 출력만
            await asyncio.sleep(2)

        print(f"[{actor_id}] 완료")

    except Exception as e:
        print(f"[{actor_id}] 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await executor.close()


async def main() -> None:
    """메인 엔트리포인트"""

    # 프로필 설정 로드
    with open('config/profiles.yaml', 'r', encoding='utf-8') as f:
        profiles_config = yaml.safe_load(f)

    num_profiles = int(os.getenv('NUM_PROFILES', profiles_config.get('num_profiles', 3)))

    print(f"총 {num_profiles}개 프로필 실행")

    # 타겟 URL (테스트용)
    target_url = input("타겟 커뮤니티 URL: ").strip()
    if not target_url:
        print("URL이 입력되지 않았습니다.")
        return

    # 전역 상태
    global_state = GlobalState()

    # 프로필별 설정 생성
    profile_configs = []
    for i in range(num_profiles):
        actor_id = f"profile_{i+1:03d}"
        profile_configs.append({
            "actor_id": actor_id,
            "temperature": profiles_config.get('base_temperature', 0.5),
            "max_hourly_actions": profiles_config.get('base_hourly_limit', 2),
            "persona_file": profiles_config.get('profile_template', {}).get('persona_file', 'config/personas/default.yaml')
        })

    # N개 프로필 동시 실행
    tasks = [
        run_actor(config["actor_id"], config, global_state, target_url)
        for config in profile_configs
    ]

    await asyncio.gather(*tasks)

    print("전체 실행 완료")


if __name__ == "__main__":
    asyncio.run(main())
