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
| `experiments/` | 탐색 비용 CSV, SVG 그래프, 비교 그림 PDF |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make experiment` · `make compare-experiment` |

현재 저장소에는 과제 1–8단계의 구현과 실험 결과가 포함되어 있습니다.

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (포트 8000, 개별 체이닝) | `make serve` |
| 웹 서버 (포트 8000, 선형 탐지) | `make serve TABLE=linear` |
| 체이닝 적재율 실험 | `make experiment` |
| 두 테이블 비교 실험 | `make compare-experiment` |
| 놓친 단계 따라잡기 (1–8) | `sh tools/catchup.sh <단계 번호>` |

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.
서버에서 `/table`을 열면 URL→코드 테이블과 호너 해시 계산 과정을 볼 수 있습니다.
개별 체이닝 화면은 노드를 화살표로 잇고, 선형 탐지 화면은 탐색 중 살펴본 슬롯을 표시합니다.
Codespaces 프록시가 전달한 호스트와 프로토콜이 유효하면 결과에 복사 가능한 전체 단축 주소를 표시합니다.

## 적재율 실험

`make experiment`는 별도 체이닝에서 적재율 0.25–4.00의 성공/실패 탐색 노드 수를
측정하고 이론값(`성공 1 + α/2`, `실패 α`)과 비교합니다. 결과 표는
`experiments/results.csv`, 그래프는 `experiments/results.svg`에 생성됩니다.
칸 수를 4093으로 고정한 실제 `HashTable`을 사용합니다. 삽입한 모든 URL과 별도로
생성한 미삽입 URL 2,000개의 탐색 경로에서 실제 비교 노드 수를 셉니다.

`make compare-experiment`는 두 구현에 같은 삽입 URL과 미삽입 URL을 사용합니다.
칸 수 4093, 적재율 0.1–0.9, 시드 2026으로 5회 반복한 평균을 이론과 비교합니다.
결과는 `experiments/table_comparison.csv`, `experiments/table_comparison.svg`,
그리고 비교 그림 한 쪽을 담은 `experiments/table_comparison.pdf`에 저장됩니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
