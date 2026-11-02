ACS–MBC 화면·사운드 전환 연동 제안서
이 문서와 `mbs_server.py`는 연동 협의를 위한 목업입니다. API 경로, 필드, 응답 및 중복 처리 방식은 양측 합의 후 확정합니다. ACS는 요청을 보내는 클라이언트이고, MBC는 HTTP 요청을 받는 서버입니다. 카메라 전환은 운영자가 직접 합니다.
동작
ACS 시퀀스가 설정된 화면 전환 시점에 도달합니다.
ACS는 설정된 MBC IP·포트로 장면·사운드 ID와 요청 ID를 전송합니다.
MBC는 요청을 접수하면 HTTP 성공 응답을 보냅니다.
ACS는 성공 응답을 받으면 연결된 다음 시퀀스 단계로 진행합니다.
성공 응답은 요청 접수를 의미하며, 실제 영상·사운드 전환 완료를 기다리지 않습니다. 전환 완료 여부를 확인해야 한다면 별도 응답·이벤트 규약이 필요합니다.
목업 요청
`POST http://<MBC IP>:<포트>/api/scenes/change`
`Content-Type: application/json`
```json
{
  "request_id": "a-123456789abc",
  "scene_id": "scene_03",
  "sound_id": "sound_02"
}
```
필드	타입	설명
`request_id`	문자열	ACS가 자동 생성하는 요청 식별자. 같은 요청을 운영자가 재시도하면 동일한 ID 사용
`scene_id`	문자열, 선택	MBC가 전환할 장면 식별자
`sound_id`	문자열, 선택	MBC가 전환할 사운드 식별자
`request_id`는 필수이며, `scene_id`와 `sound_id` 중 하나 이상이 필요합니다. 선택하지 않은 ID는 요청에서 생략합니다. IP와 포트는 ACS 설정 화면에서 지정합니다.
```json
{"request_id":"scene-only-1","scene_id":"scene_03"}
```
```json
{"request_id":"sound-only-1","sound_id":"sound_02"}
```
목업 응답
성공 시 HTTP `200`:
```json
{"accepted": true, "request_id": "a-123456789abc"}
```
현재 ACS는 응답의 HTTP 상태가 2xx이면 접수 성공으로 처리하며 응답 본문은 검증하지 않습니다. 2xx가 아닌 상태, 연결 오류 또는 타임아웃은 실패로 처리합니다. 기본 HTTP 대기 시간은 30초입니다.
HTTP 상태	목업 의미
`200`	요청 접수, 또는 동일 요청 ID와 내용의 재요청
`400`	필수 필드 누락 또는 잘못된 JSON
`404`	잘못된 API 경로
`409`	기존 요청 ID를 다른 내용으로 재사용
`503`	오류 모드로 실행 중
오류나 무응답 시 ACS는 해당 스텝에서 멈추고 운영자의 재시도·다음·중단 선택을 기다립니다. 타임아웃은 MBC가 요청을 받지 않았다는 증거가 아닙니다. ACS는 재시도 때 같은 `request_id`를 사용하므로, MBC 서버도 같은 ID의 중복 요청을 재실행하지 않는 방식으로 구현하는 것을 제안합니다.
목업 서버 실행
Python 3 표준 라이브러리만 필요합니다. `mbs_server.py`를 MBC 측 PC에 복사한 뒤:
```bash
python3 mbs_server.py --host 0.0.0.0 --port 8081
```
MBC PC의 IP와 포트를 ACS 설정에 입력합니다. 서버는 접수한 JSON을 터미널에 기록하고 실제 화면이나 사운드를 바꾸지는 않습니다.
```bash
# 같은 PC에서 직접 확인
curl -X POST http://127.0.0.1:8081/api/scenes/change \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"test-001","scene_id":"scene_03","sound_id":"sound_02"}'

# 서버 오류 모사
python3 mbs_server.py --port 8081 --mode error

# 응답 지연 모사 — ACS의 기본 30초 대기 초과
python3 mbs_server.py --port 8081 --delay 35
```
목업의 중복 요청 기록은 프로세스 메모리에만 있어 재시작하면 사라집니다. 실제 MBC 서버의 중복 처리 범위와 보관 기간은 별도 협의가 필요합니다.
양측에서 확정할 항목
실제 API 경로·포트, HTTP 또는 HTTPS, 인증 방식
`scene_id`와 `sound_id` 목록 및 각각의 자료형, 하나만 보내는 요청 형식
성공 응답을 요청 접수로 확정할지, 화면 전환 완료 통지가 필요한지
`request_id` 중복 처리의 범위와 보관 기간
오류 코드·응답 형식, 허용 지연, 연결 실패 시 운영 절차
