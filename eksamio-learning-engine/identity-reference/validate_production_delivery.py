#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Mapping

from production_delivery import (
    DeliveryExecutionDisabled,
    DeliveryProviderFailure,
    ProductionDeliveryRouter,
    SmsRuDeliveryProvider,
    SmsRuRuntimeConfig,
    YandexPostboxDeliveryProvider,
    YandexPostboxRuntimeConfig,
)


class FakeJsonTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last: tuple[str, Mapping[str, str], Mapping[str, Any], float] | None = None
        self.fail = False

    def post_json(self, *, url, headers, body, timeout_seconds):
        self.calls += 1
        self.last = (url, headers, body, timeout_seconds)
        if self.fail:
            raise TimeoutError("fixture timeout contains no request body")
        return {"MessageId": "mail-fixture-1"}


class FakeFormTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last: tuple[str, Mapping[str, str], float] | None = None
        self.fail = False

    def post_form(self, *, url, fields, timeout_seconds):
        self.calls += 1
        self.last = (url, fields, timeout_seconds)
        if self.fail:
            raise TimeoutError("fixture timeout contains no form body")
        number = fields["to"]
        return {
            "status": "OK",
            "status_code": 100,
            "sms": {
                number: {
                    "status": "OK",
                    "status_code": 100,
                    "sms_id": "sms-fixture-1",
                }
            },
        }


def expect(exc_type: type[BaseException], fn) -> str:
    try:
        fn()
    except exc_type as exc:
        return str(exc)
    raise AssertionError(f"expected {exc_type.__name__}")


def main() -> int:
    iam_secret = "IAM_FIXTURE_SECRET_SHOULD_NEVER_APPEAR"
    sms_secret = "SMSRU_FIXTURE_SECRET_SHOULD_NEVER_APPEAR"
    email_contact = "learner-fixture@example.test"
    phone_contact = "+7 925 507-06-02"
    code = "654321"

    email_transport = FakeJsonTransport()
    sms_transport = FakeFormTransport()

    email_off = YandexPostboxDeliveryProvider(
        config=YandexPostboxRuntimeConfig(
            sender_address="login@eksamio.example",
            iam_token_provider=lambda: iam_secret,
            execution_enabled=False,
        ),
        transport=email_transport,
    )
    sms_off = SmsRuDeliveryProvider(
        config=SmsRuRuntimeConfig(api_id=sms_secret, execution_enabled=False),
        transport=sms_transport,
    )
    assert "disabled" in expect(
        DeliveryExecutionDisabled,
        lambda: email_off.deliver(channel="email", contact=email_contact, code=code, challenge_id="ch:1"),
    )
    assert "disabled" in expect(
        DeliveryExecutionDisabled,
        lambda: sms_off.deliver(channel="phone", contact=phone_contact, code=code, challenge_id="ch:2"),
    )
    assert email_transport.calls == 0
    assert sms_transport.calls == 0

    email_on = YandexPostboxDeliveryProvider(
        config=YandexPostboxRuntimeConfig(
            sender_address="login@eksamio.example",
            iam_token_provider=lambda: iam_secret,
            execution_enabled=True,
        ),
        transport=email_transport,
    )
    sms_on = SmsRuDeliveryProvider(
        config=SmsRuRuntimeConfig(api_id=sms_secret, sender_name="Eksamio", execution_enabled=True),
        transport=sms_transport,
    )
    router = ProductionDeliveryRouter(email_provider=email_on, phone_provider=sms_on)

    email_ref = router.deliver(channel="email", contact=email_contact, code=code, challenge_id="ch:3")
    sms_ref = router.deliver(channel="phone", contact=phone_contact, code=code, challenge_id="ch:4")
    assert email_ref == "postbox:mail-fixture-1"
    assert sms_ref == "smsru:sms-fixture-1"

    assert email_transport.last is not None
    email_url, email_headers, email_body, email_timeout = email_transport.last
    assert email_url == "https://postbox.cloud.yandex.net/v2/email/outbound-emails"
    assert email_headers["X-YaCloud-SubjectToken"] == iam_secret
    assert email_body["Destination"]["ToAddresses"] == [email_contact]
    assert code in email_body["Content"]["Simple"]["Body"]["Text"]["Data"]
    assert 0 < email_timeout <= 30

    assert sms_transport.last is not None
    sms_url, sms_fields, sms_timeout = sms_transport.last
    assert sms_url == "https://sms.ru/sms/send"
    assert sms_fields["api_id"] == sms_secret
    assert sms_fields["to"] == "79255070602"
    assert sms_fields["json"] == "1"
    assert code in sms_fields["msg"]
    assert 0 < sms_timeout <= 30

    adapter_repr = "\n".join((repr(email_on), repr(sms_on), repr(email_on.config), repr(sms_on.config)))
    assert iam_secret not in adapter_repr
    assert sms_secret not in adapter_repr
    assert email_contact not in adapter_repr
    assert phone_contact not in adapter_repr
    assert code not in adapter_repr
    assert email_contact not in repr(vars(email_on))
    assert phone_contact not in repr(vars(sms_on))
    assert code not in repr(vars(email_on))
    assert code not in repr(vars(sms_on))

    email_transport.fail = True
    failure = expect(
        DeliveryProviderFailure,
        lambda: email_on.deliver(channel="email", contact=email_contact, code=code, challenge_id="ch:5"),
    )
    assert email_contact not in failure and code not in failure and iam_secret not in failure
    email_transport.fail = False

    sms_transport.fail = True
    failure = expect(
        DeliveryProviderFailure,
        lambda: sms_on.deliver(channel="phone", contact=phone_contact, code=code, challenge_id="ch:6"),
    )
    assert phone_contact not in failure and code not in failure and sms_secret not in failure
    sms_transport.fail = False

    bad_response_transport = FakeFormTransport()
    bad_response_transport.post_form = lambda **_: {"status": "ERROR", "status_code": 201}
    bad_sms = SmsRuDeliveryProvider(
        config=SmsRuRuntimeConfig(api_id=sms_secret, execution_enabled=True),
        transport=bad_response_transport,
    )
    failure = expect(
        DeliveryProviderFailure,
        lambda: bad_sms.deliver(channel="phone", contact=phone_contact, code=code, challenge_id="ch:7"),
    )
    assert phone_contact not in failure and code not in failure and sms_secret not in failure

    print("SEP1_PASSWORDLESS_PRODUCTION_DELIVERY=PASS")
    print("postbox_iam_request_contract=PASS")
    print("smsru_https_json_contract=PASS")
    print("execution_disabled_by_default=PASS")
    print("email_phone_route_selection=PASS")
    print("secret_contact_code_redaction=PASS")
    print("provider_failure_fail_closed=PASS")
    print("real_email_sends=0")
    print("real_sms_sends=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
