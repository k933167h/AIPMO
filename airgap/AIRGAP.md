# 폐쇄망(air-gap) 반입·설치 가이드

이 저장소는 인터넷이 없는 발주기관 내부망에 설치·운영할 수 있다. 반입은 인터넷이 되는 **빌드 PC**에서 번들을 만들고, 폐쇄망에서는 **번들만으로** 검증·설치·자체시험한다. 키트(`airgap/airgap.py`)는 Python 표준 라이브러리만 쓴다.

설정은 `airgap/airgap.json`에 있다. 순서는 K-PVOS 도구체계의 폐쇄망 반입 절차와 같다: 라이선스 검토 → 체크섬 → 내부 미러 → SBOM → PoC 증빙 → 버전 고정.

## 1. 빌드 PC(인터넷 가능)에서 번들 생성

```bash
python airgap/airgap.py bundle --with-tests          # wheel+소스+SBOM+lock
python airgap/airgap.py bundle --with-tests --images  # + docker 이미지(docker 필요)
```

`dist/<이름>-airgap-<커밋>.tar.gz`(+ `.sha256`)가 나온다. 담기는 것:

| 항목 | 내용 |
|---|---|
| `wheelhouse/` | 의존성 wheel 전부(대상 Python·플랫폼 고정, 바이너리만) + 이 저장소의 프로젝트 wheel |
| `requirements.lock` | 해시 고정 목록(`pip --require-hashes`) |
| `source.tar` | 저장소 소스(`git archive HEAD`) |
| `sbom.cdx.json` | CycloneDX 1.6 SBOM(wheel 메타데이터·SHA-256·라이선스) |
| `images/*.tar` | (`--images`) 앱 이미지 + 외부 이미지(`docker save`) |
| `manifest.json` | 대상 Python·플랫폼·패키지 수·라이선스 경고 |
| `SHA256SUMS` | 번들 내부 전 파일 해시 |

빌드 로그에 금지 라이선스(AGPL·SSPL·BUSL·ELv2·Commons Clause) 해당·라이선스 미상 목록이 뜨면 반입 전에 검토한다.

## 2. 반입 매체로 폐쇄망에 옮긴 뒤, 검증

```bash
python airgap/airgap.py verify dist/<이름>-airgap-<커밋>.tar.gz
```

`.tar.gz.sha256`과 내부 `SHA256SUMS`를 모두 대조한다. 변조·누락·목록 밖 파일이 0이어야 한다.

## 3. 설치(네트워크 없이)

```bash
python airgap/airgap.py install dist/<이름>-airgap-<커밋>/ --venv /opt/<이름>/venv
```

`pip install --no-index --require-hashes`로 wheelhouse에서만 설치한다. 외부 인덱스에 접속하지 않는다. 대상 Python 버전(`manifest.json`의 `python`)에 맞는 인터프리터를 자동으로 고른다. 컨테이너로 운영하면 `images/*.tar`를 `docker load` 후 compose로 올린다.

## 4. 기동 전 점검

```bash
python airgap/airgap.py preflight --env-file .env     # 외부 주소·비밀값 점검
python airgap/airgap.py egress-check --env-file .env   # 외부 주소만 점검
```

- `*_URL`·`*_HOST`·`*_ISSUER` 같은 설정이 내부 주소(사설 IP·`.internal` 등)·단일 레이블 서비스명을 가리키는지 확인한다. 외부 주소가 있으면 알려준다.
- 비밀값이 비었거나 기본값(`change-me`, `replace-with-…`)이거나 너무 짧으면 막는다.
- 허용 외부 호스트가 있으면 `AIRGAP_ALLOWED_HOSTS=a.internal,b.internal`로 지정한다.

## 5. 자체시험(폐쇄망에서 설치 즉시)

```bash
# 네트워크가 실제로 차단됐는지까지 확인하려면 격리 환경에서:
unshare -rn python3 airgap/airgap.py selftest dist/<이름>-airgap-<커밋>/ --require-offline
```

검증 → 오프라인 설치 → 시험 → `/health` 기동 확인을 한 번에 돌리고 `selftest-report.json`을 남긴다. 이 보고서는 증빙 레코드(A6·SER-004)로 보관한다.

## 주의

- 번들은 대상 OS·Python에 맞는 바이너리 wheel을 담는다. 대상이 다르면 `airgap.json`의 `platforms`·`python`을 맞춰 다시 번들한다.
- `--images` 없이 만들면 소스·wheel만 담긴다. 컨테이너 운영에는 `--images`가 필요하고 빌드 PC에 docker가 있어야 한다.
- 외부 이미지(PostgreSQL·Prometheus·Grafana 등)는 각자의 라이선스로 반입하며, 번들은 `docker save`로 복사만 한다.
