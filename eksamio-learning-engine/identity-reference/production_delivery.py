#!/usr/bin/env python3
"""Production-shaped passwordless delivery adapters for Eksamio Pro.

The adapters remain transport-injected and execution-disabled by default. They
never persist contacts or verification codes and never become canonical identity
authority; they only implement the structural ``DeliveryProvider.deliver``
contract used by the merged passwordless identity service.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


class DeliveryError(ValueError):
    pass


class DeliveryExecutionDisabled(DeliveryError):
    pass


class DeliveryProviderFailure(DeliveryError):
    pass


class JsonPostTransport(Protocol):
    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class FormPostTransport(Protocol):
    def post_form(
        self,
        *,
        url: str,
        fields: Mapping[str, str],
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class YandexPostboxRuntimeConfig:
    sender_address: str
    iam_token_provider: Callable[[], str] = field(repr=False, compare=False)
    endpoint: str = "https://postbox.cloud.yandex.net/v2/email/outbound-emails"
    timeout_seconds: float = 10.0
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if "@" not in self.sender_address:
            raise ValueError("verified sender e-mail address is required")
        if not self.endpoint.startswith("https://"):
            raise ValueError("Postbox endpoint must use HTTPS")
        if not 0 < self.timeout_seconds <= 30:
            raise ValueError("Postbox timeout must be in (0, 30]")


@dataclass(frozen=True)
class SmsRuRuntimeConfig:
    api_id: str = field(repr=False)
    sender_name: str | None = None
    endpoint: str = "https://sms.ru/sms/send"
    timeout_seconds: float = 10.0
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.api_id:
            raise ValueError("SMS.RU api_id is required")
        if not self.endpoint.startswith("https://"):
            raise ValueError("SMS.RU endpoint must use HTTPS")
        if not 0 < self.timeout_seconds <= 30:
            raise ValueError("SMS.RU timeout must be in (0, 30]")


class YandexPostboxDeliveryProvider:
    def __init__(self, *, config: YandexPostboxRuntimeConfig, transport: JsonPostTransport) -> None:
        self.config = config
        self.transport = transport

    def __repr__(self) -> str:
        return (
            f"YandexPostboxDeliveryProvider(sender_address={self.config.sender_address!r}, "
            f"endpoint={self.config.endpoint!r}, execution_enabled={self.config.execution_enabled!r}, "
            "credentials='<redacted>')"
        )

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        if channel != "email":
            raise DeliveryProviderFailure("Postbox adapter accepts e-mail channel only")
        if not self.config.execution_enabled:
            raise DeliveryExecutionDisabled("production e-mail delivery is disabled")
        token = self.config.iam_token_provider()
        if not isinstance(token, str) or not token:
            raise DeliveryProviderFailure("Postbox IAM credential unavailable")
        if not contact or "@" not in contact or not code or not challenge_id:
            raise DeliveryProviderFailure("invalid e-mail delivery input")

        body = {
            "FromEmailAddress": self.config.sender_address,
            "Destination": {"ToAddresses": [contact]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": "Код входа Eksamio", "Charset": "UTF-8"},
                    "Body": {
                        "Text": {
                            "Data": f"Код входа: {code}. Если вы не запрашивали вход, проигнорируйте письмо.",
                            "Charset": "UTF-8",
                        }
                    },
                }
            },
        }
        try:
            response = self.transport.post_json(
                url=self.config.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "X-YaCloud-SubjectToken": token,
                },
                body=body,
                timeout_seconds=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise DeliveryProviderFailure("Postbox delivery transport failed") from exc

        message_id = response.get("MessageId") or response.get("messageId")
        if not isinstance(message_id, str) or not message_id:
            raise DeliveryProviderFailure("Postbox response did not contain a message id")
        return f"postbox:{message_id}"


class SmsRuDeliveryProvider:
    def __init__(self, *, config: SmsRuRuntimeConfig, transport: FormPostTransport) -> None:
        self.config = config
        self.transport = transport

    def __repr__(self) -> str:
        return (
            f"SmsRuDeliveryProvider(endpoint={self.config.endpoint!r}, "
            f"sender_name={self.config.sender_name!r}, execution_enabled={self.config.execution_enabled!r}, "
            "api_id='<redacted>')"
        )

    @staticmethod
    def _sms_number(contact: str) -> str:
        digits = "".join(ch for ch in contact if ch.isdigit())
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        if len(digits) != 11 or not digits.startswith("7"):
            raise DeliveryProviderFailure("phone must normalize to Russian E.164 form")
        return digits

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        if channel != "phone":
            raise DeliveryProviderFailure("SMS.RU adapter accepts phone channel only")
        if not self.config.execution_enabled:
            raise DeliveryExecutionDisabled("production SMS delivery is disabled")
        if not code or not challenge_id:
            raise DeliveryProviderFailure("invalid SMS delivery input")
        number = self._sms_number(contact)
        fields = {
            "api_id": self.config.api_id,
            "to": number,
            "msg": f"Eksamio: код входа {code}",
            "json": "1",
        }
        if self.config.sender_name:
            fields["from"] = self.config.sender_name
        try:
            response = self.transport.post_form(
                url=self.config.endpoint,
                fields=fields,
                timeout_seconds=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise DeliveryProviderFailure("SMS.RU delivery transport failed") from exc

        if response.get("status") != "OK" or int(response.get("status_code", 0)) != 100:
            raise DeliveryProviderFailure("SMS.RU rejected the delivery request")
        sms = response.get("sms")
        if not isinstance(sms, Mapping):
            raise DeliveryProviderFailure("SMS.RU response did not contain sms result")
        row = sms.get(number)
        if not isinstance(row, Mapping) or row.get("status") != "OK" or int(row.get("status_code", 0)) != 100:
            raise DeliveryProviderFailure("SMS.RU did not accept the target message")
        sms_id = row.get("sms_id")
        if not isinstance(sms_id, str) or not sms_id:
            raise DeliveryProviderFailure("SMS.RU response did not contain sms_id")
        return f"smsru:{sms_id}"


class ProductionDeliveryRouter:
    """Provider-neutral adapter matching the existing DeliveryProvider protocol."""

    def __init__(self, *, email_provider: YandexPostboxDeliveryProvider, phone_provider: SmsRuDeliveryProvider) -> None:
        self.email_provider = email_provider
        self.phone_provider = phone_provider

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        if channel == "email":
            return self.email_provider.deliver(
                channel=channel, contact=contact, code=code, challenge_id=challenge_id
            )
        if channel == "phone":
            return self.phone_provider.deliver(
                channel=channel, contact=contact, code=code, challenge_id=challenge_id
            )
        raise DeliveryProviderFailure("unsupported passwordless delivery channel")
