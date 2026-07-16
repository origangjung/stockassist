from datetime import datetime, timezone


DISCLAIMER = (
    "\ubcf8 \uc815\ubcf4\ub294 \ud22c\uc790 \ud310\ub2e8\uc744 \uc704\ud55c \ucc38\uace0 \uc815\ubcf4\uc774\uba70, "
    "\ud22c\uc790 \uc790\ubb38\uc774\ub098 \ub9e4\ub9e4 \uc9c0\uc2dc\uac00 \uc544\ub2d9\ub2c8\ub2e4. "
    "\ud22c\uc790 \uacb0\uacfc\uc5d0 \ub300\ud55c \ucc45\uc784\uc740 \ud22c\uc790\uc790 \ubcf8\uc778\uc5d0\uac8c \uc788\uc2b5\ub2c8\ub2e4."
)


def compliance_metadata() -> dict[str, str | bool]:
    return {
        "data_as_of": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER,
        "is_investment_advice": False,
    }
