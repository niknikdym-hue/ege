#!/usr/bin/env python3
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_PATH = ROOT / "tilda-ready/pages/registration/registration-T123.txt"
INSTALL_PATH = ROOT / "tilda-ready/pages/registration/registration-INSTALLATION.txt"


class InputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "input":
            self.inputs.append({key: value for key, value in attrs})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def checkbox_by_id(inputs: list[dict[str, str | None]], element_id: str) -> dict[str, str | None]:
    matches = [node for node in inputs if node.get("type") == "checkbox" and node.get("id") == element_id]
    require(len(matches) == 1, f"expected exactly one checkbox #{element_id}")
    return matches[0]


def main() -> None:
    source = UI_PATH.read_text(encoding="utf-8")
    installation = INSTALL_PATH.read_text(encoding="utf-8")

    parser = InputParser()
    parser.feed(source)
    checkboxes = [node for node in parser.inputs if node.get("type") == "checkbox"]
    require(len(checkboxes) == 2, "registration UI must contain exactly two checkboxes")

    pd = checkbox_by_id(checkboxes, "er-pd")
    marketing = checkbox_by_id(checkboxes, "er-marketing")
    require("required" in pd, "personal-data consent must be required")
    require("required" not in marketing, "marketing consent must remain optional")
    require("checked" not in marketing, "marketing consent must be unchecked by default")

    forbidden = (
        "localStorage",
        "sessionStorage",
        "demo-continuity",
        "anonymous-continuity",
        "guest_identity",
        "Authorization: Bearer",
    )
    for needle in forbidden:
        require(needle not in source, f"forbidden browser/auth continuity pattern: {needle}")

    require("credentials:'include'" in source or 'credentials:"include"' in source,
            "registration HTTP requests must include credentials")
    require("post('/v1/registration/begin',payload)" in source,
            "begin endpoint must be wired through the credentialed POST helper")
    require("post('/v1/registration/verify',{challenge_id:challengeId,code:code})" in source,
            "verify endpoint must be wired through the credentialed POST helper")

    begin_fields = (
        "email:email.value.trim()",
        "personal_data_consent:true",
        "marketing_consent:Boolean(marketing.checked)",
        "personal_data_document_version:String(config.personalDataDocumentVersion)",
        "personal_data_text_version:String(config.personalDataTextVersion)",
        "marketing_document_version:String(config.marketingDocumentVersion)",
        "marketing_text_version:String(config.marketingTextVersion)",
        "client_request_id:clientRequestId",
    )
    for field in begin_fields:
        require(field in source, f"missing begin payload contract: {field}")

    require("if(url.protocol!=='https:')return '';" in source,
            "API base must fail closed unless HTTPS")
    require("if(!configured){pd.disabled=true;marketing.disabled=true;email.disabled=true;}" in source,
            "form must fail closed when deployment configuration is incomplete")
    require("beginButton.disabled=!configured;" in source,
            "begin action must remain disabled until configuration validates")

    blank_defaults = (
        "apiBaseUrl:''",
        "personalDataConsentUrl:''",
        "personalDataCheckboxText:''",
        "personalDataDocumentVersion:''",
        "personalDataTextVersion:''",
        "marketingConsentUrl:''",
        "marketingCheckboxText:''",
        "marketingDocumentVersion:''",
        "marketingTextVersion:''",
    )
    for default in blank_defaults:
        require(default in source, f"legal/runtime deployment default must stay unresolved: {default}")

    require("window.crypto" in source and "randomUUID" in source,
            "client request id must be generated per browser attempt")
    require("'registration:'" in source,
            "client request id must keep an allowed stable prefix")
    require("beginLocked=true" in source,
            "idempotency request id must lock after CHALLENGE_SENT")

    require("new CustomEvent('eksamio:authenticated'" in source,
            "authenticated completion event is required for learner integration")
    require("detail:{status:'AUTHENTICATED'}" in source,
            "completion event must not expose session credentials")
    require("window.location.assign(target)" in source,
            "optional authenticated redirect must use the validated target")

    require("EXTERNAL_REVIEW_REQUIRED" in installation,
            "installation instructions must preserve legal review boundary")
    require("NOT PUBLISHED BY REPOSITORY TASK" in installation,
            "installation package must explicitly remain unpublished")
    require("marketing_consent — optional and unchecked by default" in installation,
            "installation instructions must preserve optional marketing consent")
    require("HttpOnly; Secure; SameSite=Lax" in installation,
            "installation instructions must preserve server-owned session-cookie contract")

    # Ensure the client-request-id shape produced by the UI fits the server validator.
    generated_example = "registration:123e4567-e89b-12d3-a456-426614174000"
    require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,159}", generated_example)),
            "generated client request id must fit the registration server contract")

    print("registration UI gate: PASS")


if __name__ == "__main__":
    main()
