# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2의 **시작 저장소**입니다.
채팅창에 묻고 복사·붙여넣기 하던 방식에서 벗어나, Codespace 안의 에이전트가
저장소를 읽고, 파일을 고치고, 테스트를 직접 돌리게 하는 방법을 익힙니다.

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)
- 해시 테이블 복습: [주제 08 해시 테이블](https://lec-algorithm.github.io/lecture/course/topic-08-hashing/)

## 시작하기

1. 이 저장소 상단의 **Use this template** → **Create a new repository**
2. 저장소 이름은 `algorithms-hw2`처럼 정합니다. 공개(Public)로 만듭니다.
3. 만들어진 **내 저장소**에서 **Code** → **Codespaces** 탭 → **Create codespace on main**
4. 왼쪽 막대의 Copilot 아이콘을 눌러 채팅 창을 열고, 창 아래쪽에서 **Agent** 모드를 고릅니다.

## 들어 있는 것

| 파일 | 하는 일 |
| --- | --- |
| `SPEC.md` | URL 단축기와 두 해시 테이블의 동작 명세 |
| `PLAN.md` | 구현 순서와 검증 계획 |
| `src/` | base62, 해시 테이블, URL 단축기, 웹 서버 |
| `tests/` | 두 구현과 서버의 경계 사례 테스트 |
| `experiments/` | 탐색 비용 CSV, SVG 그래프, PDF 보고서 |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make experiment` · `make compare-experiment` |

현재 저장소에는 과제 1–8단계의 구현과 실험 결과가 포함되어 있습니다.

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (포트 8000) | `make serve` |
| 체이닝 적재율 실험 | `make experiment` |
| 두 테이블 비교 실험 | `make compare-experiment` |
| 놓친 단계 따라잡기 (1–8) | `sh tools/catchup.sh <단계 번호>` |

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.
서버에서 `/table`을 열면 저장된 해시 테이블과 다항식 해시 계산 과정을 볼 수 있습니다.
`make compare-experiment`는 두 충돌 처리 방식의 탐색 비용 표, SVG 그래프, 1쪽 PDF 보고서를
`experiments/`에 생성합니다.

## 적재율 실험

`make experiment`는 별도 체이닝에서 적재율 0.25–4.00의 성공/실패 탐색 노드 수를
측정하고 이론값(`성공 1 + α/2`, `실패 α`)과 비교합니다. 결과 표는
`experiments/probe_results.csv`, 그래프는 `experiments/probe_results.svg`에 생성됩니다.
성공 탐색은 유한한 무작위 키 집합의 버킷 분포 때문에 이론값과 조금 다를 수 있으며,
실패 탐색은 모든 버킷을 한 번씩 확인해 평균하므로 이 실험에서 이론값과 일치합니다.

`make compare-experiment`는 같은 키 집합을 별도 체이닝과 선형 탐지에 넣고 적재율
0.1–0.9의 성공/실패 탐색 비용을 비교합니다. 결과는
`experiments/table_comparison.csv`, `experiments/table_comparison.svg`, 그리고
최대 2쪽인 `experiments/table_comparison.pdf`에 저장됩니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
