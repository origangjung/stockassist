/** office-map.config 파일은 프론트 기능 상태와 이벤트 기능을 담당한다. */

import type { MeetingAgentKey } from "../../components/analysis/agent-meeting-stage";

export type OfficeRoomId = "analysts" | "research" | "trading" | "risk" | "pm";
export type OfficeMotion = "typing" | "reading" | "scanning" | "debating" | "presenting" | "trading" | "guarding" | "patrolling" | "weighing" | "approving";

/** 사무실 구역의 식별자, 화면 라벨, CSS 배치 클래스를 연결하는 설정 계약입니다. */
export interface OfficeRoom {
  id: OfficeRoomId;
  label: string;
  /** Name 클래스는 화면 기능별 상태와 도메인 이벤트를 관리합니다.의 상태와 동작을 캡슐화합니다. */
  className: string;
}

/**
 * 사무실 캐릭터의 소개 문구, 담당 AI, 동작 종류와 퍼센트 좌표를 정의합니다.
 * agent가 없는 캐릭터는 보조 연출용이고, 있는 캐릭터는 실제 분석 이벤트와 연결됩니다.
 */
export interface OfficeCharacter {
  id: string;
  name: string;
  role: string;
  intro: string;
  motion: OfficeMotion;
  room: OfficeRoomId;
  agent?: MeetingAgentKey | "director";
  x: number;
  y: number;
}

/** `officeRooms`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const officeRooms: OfficeRoom[] = [
  { id: "analysts", label: "ANALYSTS", className: "office-room--analysts" },
  { id: "research", label: "RESEARCH", className: "office-room--research" },
  { id: "trading", label: "TRADING", className: "office-room--trading" },
  { id: "risk", label: "RISK MGMT", className: "office-room--risk" },
  { id: "pm", label: "PM OFFICE", className: "office-room--pm" },
];

/** `officeCharacters`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const officeCharacters: OfficeCharacter[] = [
  { id: "chart", name: "차트", role: "기술 AI", intro: "가격과 거래량에서 추세와 모멘텀을 점검합니다.", motion: "scanning", room: "analysts", agent: "technical", x: 13, y: 34 },
  { id: "news", name: "뉴스", role: "뉴스 AI", intro: "뉴스와 공시의 시점별 영향을 확인합니다.", motion: "reading", room: "analysts", agent: "news", x: 24, y: 34 },
  { id: "sentiment", name: "민심", role: "이벤트 리서처", intro: "시장 반응과 기사 흐름의 방향을 교차 확인합니다.", motion: "typing", room: "analysts", x: 35, y: 34 },
  { id: "ledger", name: "장부", role: "재무 AI", intro: "공개 시점 기준 실적과 재무 건전성을 검토합니다.", motion: "reading", room: "analysts", agent: "financial", x: 46, y: 34 },
  { id: "bull", name: "불불이", role: "강세 리서처", intro: "긍정 신호가 유지될 조건과 상승 근거를 주장합니다.", motion: "debating", room: "research", x: 61, y: 34 },
  { id: "bear", name: "곰곰이", role: "약세 리서처", intro: "낙관적 결론의 빈틈과 반대 근거를 검증합니다.", motion: "debating", room: "research", x: 72, y: 34 },
  { id: "lead", name: "팀장님", role: "리서치 팀장", intro: "강세와 약세 의견의 근거 수준을 비교합니다.", motion: "presenting", room: "research", x: 83, y: 34 },
  { id: "trader", name: "트레이더", role: "시장 실행 검토", intro: "유동성과 가격 구간을 참고 정보로 정리합니다.", motion: "trading", room: "trading", x: 18, y: 76 },
  { id: "volguard", name: "볼가드", role: "위험 AI", intro: "변동성과 하락 위험, 시장 국면을 경고합니다.", motion: "guarding", room: "risk", agent: "risk", x: 48, y: 75 },
  { id: "averaging", name: "물타기 감시자", role: "위험 통제", intro: "손실 확대와 무리한 추격 행동을 경계합니다.", motion: "patrolling", room: "risk", x: 59, y: 75 },
  { id: "balance", name: "저울추", role: "수급 AI", intro: "공매도와 투자자 흐름의 변화 방향을 분석합니다.", motion: "weighing", room: "risk", agent: "investor_flow", x: 69, y: 75 },
  { id: "chair", name: "회장님", role: "종합 판단", intro: "통과한 전문 AI의 근거만 모아 최종 참고 의견을 정리합니다.", motion: "approving", room: "pm", agent: "director", x: 88, y: 76 },
];
